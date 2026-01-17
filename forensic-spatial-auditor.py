bl_info = {
    "name": "Forensic Spatial Auditor",
    "author": "Blendervisualinvestigation.com",
    "version": (1, 2, 1),
    "blender": (4, 2, 0),
    "location": "View3D > N-Panel > View",
    "description": "Quantified Uncertainty Budget for Aerial Reconstruction",
    "category": "3D View",
}

import bpy
import math
from bpy.props import FloatProperty, StringProperty, CollectionProperty, IntProperty, EnumProperty, PointerProperty
from bpy.types import Panel, UIList, Operator, PropertyGroup

# ------------------------------------------------------------------------
#    Data Structures
# ------------------------------------------------------------------------

class RSSMeasurementReading(PropertyGroup):
    value: FloatProperty(name="Reading", default=0.0, precision=4)

class RSSErrorSource(PropertyGroup):
    name: StringProperty(name="Source", default="Error Source")
    value: FloatProperty(name="Uncertainty (1σ)", default=0.0, precision=4)

# ------------------------------------------------------------------------
#    Logic Helper
# ------------------------------------------------------------------------

def update_metrology_logic(self, context):
    preset = self.resolution_preset
    profile = self.conservatism_profile
    
    # 1. Image Resolution Tiers (Physical GSD Logic)
    tiers = {
        '15_30CM': (0.15, 0.30),
        '30_60CM': (0.30, 0.60),
        '1_2_5M':  (1.00, 2.50),
        '15_30M':  (15.00, 30.00),
    }
    
    # 2. Harrington Empirical Tiers (MAE %)
    harrington_rates = {
        'H_ON_ROAD': 0.0145,
        'H_OFF_ROAD': 0.0161,
    }
    
    img_res_source = next((s for s in self.error_sources if s.name == "Sensor Uncertainty"), None)
    if not img_res_source:
        img_res_source = self.error_sources.add()
        img_res_source.name = "Sensor Uncertainty"

    if preset in harrington_rates:
        values = [r.value for r in self.readings]
        mean = sum(values) / len(values) if values else 1.0
        img_res_source.value = mean * harrington_rates[preset]

    elif preset in tiers:
        min_gsd, max_gsd = tiers[preset]
        if profile == 'OPTIMISTIC': chosen_gsd = min_gsd
        elif profile == 'BALANCED': chosen_gsd = (min_gsd + max_gsd) / 2
        else: chosen_gsd = max_gsd
            
        point_error = chosen_gsd / 2
        img_res_source.value = math.sqrt(point_error**2 + point_error**2)

class RSSSettings(PropertyGroup):
    readings: CollectionProperty(type=RSSMeasurementReading)
    error_sources: CollectionProperty(type=RSSErrorSource)
    
    resolution_preset: EnumProperty(
        name="Source Data",
        items=[
            ('15_30CM', "Aerial Photography (15-30 cm)", "High-resolution sub-meter imagery"),
            ('30_60CM', "Commercial Satellite (30-60 cm)", "Standard high-res satellite data"),
            ('1_2_5M',  "Older Satellite (1.00-2.50 m)", "Legacy or mid-resolution satellite data"),
            ('15_30M',  "Landsat/Sentinel (15-30 m)", "Public access satellite (Wilderness/Oceans)"),
            ('H_ON_ROAD', "Harrington: On-Road", "Empirical 1.45% MAE for road markings"),
            ('H_OFF_ROAD', "Harrington: Off-Road", "Empirical 1.61% MAE for buildings"),
            ('CUSTOM', "Custom/Manual", "User-defined sensor uncertainty"),
        ],
        default='15_30CM', update=update_metrology_logic
    )

    conservatism_profile: EnumProperty(
        name="Profile",
        items=[
            ('OPTIMISTIC', "Optimistic", "Minimum GSD of tier"),
            ('BALANCED', "Balanced", "Midpoint GSD of tier"),
            ('DEFENSIVE', "Defensive", "Maximum GSD of tier"),
        ],
        default='DEFENSIVE', update=update_metrology_logic
    )

    sigma_multiplier: IntProperty(name="Coverage Factor (k)", default=1, min=1, max=3)

# ------------------------------------------------------------------------
#    Operators
# ------------------------------------------------------------------------

class RSS_OT_AddReading(Operator):
    bl_idname = "rss.add_reading"; bl_label = "Add Trial"
    def execute(self, context):
        context.scene.rss_settings.readings.add()
        return {'FINISHED'}

class RSS_OT_RemoveReading(Operator):
    bl_idname = "rss.remove_reading"; bl_label = "Remove"
    index: IntProperty()
    def execute(self, context):
        context.scene.rss_settings.readings.remove(self.index)
        return {'FINISHED'}

class RSS_OT_ClearReadings(Operator):
    bl_idname = "rss.clear_readings"; bl_label = "Clear All"
    def execute(self, context):
        context.scene.rss_settings.readings.clear()
        return {'FINISHED'}

class RSS_OT_CopyToClipboard(Operator):
    bl_idname = "rss.copy_methodology"
    bl_label = "Copy for Methodology"
    bl_description = "Generate and copy a forensic methodology summary to the clipboard"

    def execute(self, context):
        settings = context.scene.rss_settings
        values = [r.value for r in settings.readings]
        readings_count = len(values)
        
        if readings_count == 0:
            self.report({'WARNING'}, "No readings to export.")
            return {'CANCELLED'}

        # 1. Primary Observation Data
        mean = sum(values) / readings_count
        if readings_count >= 2:
            variance = sum((x - mean)**2 for x in values) / (readings_count - 1)
            u_observer = math.sqrt(variance)
        else:
            u_observer = 0.0

        # 2. Sensor Uncertainty
        u_sensor_sq = sum(e.value**2 for e in settings.error_sources)
        u_sensor = math.sqrt(u_sensor_sq)
        
        # 3. Combined Logic
        total_u_combined = math.sqrt(u_sensor_sq + u_observer**2)
        expanded_u = total_u_combined * settings.sigma_multiplier
        confidence = {1: "68.2%", 2: "95.4%", 3: "99.7%"}[settings.sigma_multiplier]

        # Preset info for methodology
        preset_name = dict(settings.bl_rna.properties['resolution_preset'].enum_items).get(settings.resolution_preset).name
        profile_name = dict(settings.bl_rna.properties['conservatism_profile'].enum_items).get(settings.conservatism_profile).name

        # Constructing the text
        lines = [
            "METHODOLOGY: SPATIAL UNCERTAINTY ANALYSIS",
            "-" * 40,
            f"1. OBSERVER DATA: {readings_count} trial(s) were conducted.",
            f"   - Sample Mean (μ): {mean:.4f}m",
            f"   - User Induced Uncertainty (uo): ±{u_observer:.4f}m" if readings_count >= 2 else "   - User Induced Uncertainty (uo): Insufficient trials (n < 2)",
            "",
            f"2. SENSOR BUDGET: Derived from system preset '{preset_name}' ({profile_name} profile).",
            f"   - Quantified Sensor Uncertainty (us): ±{u_sensor:.4f}m",
            "",
            "3. ERROR PROPAGATION (Root Sum Square):",
            f"   - Combined Standard Uncertainty (uc): ±{total_u_combined:.4f}m",
            f"   - Coverage Factor (k / σ): {settings.sigma_multiplier} ({confidence} confidence)",
            f"   - Final Expanded Uncertainty (U): ±{expanded_u:.4f}m",
            "",
            f"FINAL RESULT: {mean:.4f}m ± {expanded_u:.4f}m",
            "-" * 40,
            "Calculated using the Forensic Spatial Auditor (Blendervisualinvestigation.com)"
        ]

        context.window_manager.clipboard = "\n".join(lines)
        self.report({'INFO'}, "Methodology text copied to clipboard!")
        return {'FINISHED'}

# ------------------------------------------------------------------------
#    UI Panel
# ------------------------------------------------------------------------

class VIEW3D_PT_RSSMeasurement(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'View'
    bl_label = "Spatial Uncertainty Auditor"

    def draw(self, context):
        layout = self.layout
        # SAFETY CHECK: If registration failed, don't crash the UI
        if not hasattr(context.scene, "rss_settings"):
            layout.label(text="Error: Settings not registered.", icon='ERROR')
            return

        settings = context.scene.rss_settings
        
        # --- I. OBSERVATION DATA ---
        box = layout.box()
        box.label(text="I. Primary Observation Data", icon='VIEWZOOM')
        
        row = box.row()
        row.operator("rss.add_reading", icon='ADD')
        row.operator("rss.clear_readings", icon='TRASH')

        values = [r.value for r in settings.readings]
        readings_count = len(values)
        
        for i, r in enumerate(settings.readings):
            r_row = box.row(align=True)
            r_row.prop(r, "value", text=f"Trial {i+1}")
            op = r_row.operator("rss.remove_reading", text="", icon='X')
            op.index = i

        if readings_count > 0:
            mean = sum(values) / readings_count
            box.label(text=f"Sample Mean (μ): {mean:.4f}m", icon='OBJECT_ORIGIN')
            
            if readings_count >= 2:
                variance = sum((x - mean)**2 for x in values) / (readings_count - 1)
                u_observer = math.sqrt(variance)
                box.label(text=f"User Induced Uncertainty (uo): ±{u_observer:.4f}m")
            else:
                u_observer = 0.0
                box.label(text="Need 2+ trials for uo.", icon='INFO')
        else:
            mean = u_observer = 0.0

        # --- II. SENSOR UNCERTAINTY ---
        box = layout.box()
        box.label(text="II. Sensor-Induced Uncertainty", icon='IMAGE_DATA')
        box.prop(settings, "resolution_preset", text="System")
        
        # Profile only available for physical tiers
        physical_tiers = {'15_30CM', '30_60CM', '1_2_5M', '15_30M'}
        if settings.resolution_preset in physical_tiers:
            box.prop(settings, "conservatism_profile", text="Profile")

        # --- III. COMBINED BUDGET ---
        box = layout.box()
        box.label(text="III. Combined Uncertainty Budget", icon='CON_DISTLIMIT')
        
        u_sensor_sq = sum(e.value**2 for e in settings.error_sources)
        total_u_combined = math.sqrt(u_sensor_sq + u_observer**2)
        
        box.prop(settings, "sigma_multiplier", text="Coverage Factor (k / σ)")
        expanded_u = total_u_combined * settings.sigma_multiplier
        
        confidence = {1: "68.2%", 2: "95.4%", 3: "99.7%"}[settings.sigma_multiplier]
        
        res_box = box.box()
        res_box.label(text=f"Audit Result (σ={settings.sigma_multiplier} / k={settings.sigma_multiplier}):")
        res_box.label(text=f"{mean:.4f}m ± {expanded_u:.4f}m")
        res_box.label(text=f"Confidence Interval: {confidence}")

        # --- IV. EXPORT ---
        layout.separator()
        layout.operator("rss.copy_methodology", icon='COPY_ID')

# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

classes = (
    RSSMeasurementReading,
    RSSErrorSource,
    RSSSettings,
    RSS_OT_AddReading,
    RSS_OT_RemoveReading,
    RSS_OT_ClearReadings,
    RSS_OT_CopyToClipboard,
    VIEW3D_PT_RSSMeasurement,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    # Registering the pointer to the Scene
    bpy.types.Scene.rss_settings = PointerProperty(type=RSSSettings)

def unregister():
    # Remove the scene property first
    if hasattr(bpy.types.Scene, "rss_settings"):
        del bpy.types.Scene.rss_settings
    # Unregister classes in reverse
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()