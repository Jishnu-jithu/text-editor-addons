##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
##### END GPL LICENSE BLOCK #####


bl_info = {
    "name": "Textify",
    "blender": (2, 80, 0),
    "version": (1, 0, 0),
    "author": "Jithu",
    "location": "Text Editor > Sidebar",
    "description": "All-in-one tool for enhancing Blender's Text Editor",
    "category": "Text Editor",
}


import bpy
from bpy.props import BoolProperty, EnumProperty, IntProperty, StringProperty

from . import (
    addon_updater_ops,
    character_count,
    code_map,
    find_replace,
    jump_to_line,
    trim_whitespace,
    open_recent,
)


@addon_updater_ops.make_annotations
class Textify_Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    def update_cm_category(self, _):
        try:
            bpy.utils.unregister_class(code_map.CODE_MAP_PT_panel)
        except:
            pass

        code_map.CODE_MAP_PT_panel.bl_category = self.code_map_category
        bpy.utils.register_class(code_map.CODE_MAP_PT_panel)

    def update_op_category(self, _):
        try:
            bpy.utils.unregister_class(open_recent.TEXT_PT_open_recent)
        except:
            pass

        open_recent.TEXT_PT_open_recent.bl_category = self.open_recent_category
        bpy.utils.register_class(open_recent.TEXT_PT_open_recent)

    code_map_category: StringProperty(
        name="Category",
        description="Category to show Import Any panel",
        default="Code Map",
        update=update_cm_category,
    )

    open_recent_category: StringProperty(
        name="Category",
        description="Category to show Import Any panel",
        default="Text",
        update=update_op_category,
    )

    enable_character_count = BoolProperty(
        name="Enable Character Count",
        description="Enable or disable the character count",
        default=True
    )

    enable_jump_to_line = BoolProperty(
        name="Enable Jump to Line",
        description="Enable or disable the Jump to Line",
        default=True
    )

    enable_find_replace = BoolProperty(
        name="Enable Find & Replace",
        description="Enable or disable the Find & Replace",
        default=True
    )

    enable_open_recent = BoolProperty(
        name="Enable Open Recent",
        description="Enable or disable the Open Recent",
        default=True
    )

    enable_open_recent_panel = BoolProperty(
        name="Enable Open Recent Panel",
        description="Enable or disable the Open Recent panel",
        default=True
    )

    enable_code_map = BoolProperty(
        name="Enable Code Map",
        description="Enable or disable the Code Map",
        default=True
    )

    enable_trim_whitespace = BoolProperty(
        name="Enable Trim Whitespace",
        description="Enable or disable the trim whitespace",
        default=True
    )

    # Find & replace preferences
    enable_find_set_selected: bpy.props.BoolProperty(
        name="Text Selection for Finding",
        description="If enabled, the selected text will be automatically filled into the 'Find' field when the 'Find & Replace' popup is invoked.",
        default=True
    )

    enable_replace_set_selected: bpy.props.BoolProperty(
        name="Text Selection for Replacement",
        description="If enabled, the selected text will be automatically filled into the 'Replace' field when the 'Find & Replace' popup is invoked.",
        default=True
    )

    display_count_label: bpy.props.BoolProperty(
        name="Display Count Label",
        description="If enabled, the count of the found text will be displayed on popup.",
        default=True
    )

    # Code Map preferences
    show_code_filters: BoolProperty(
        name="Show Code Filters in Panel",
        description="Toggle to display the code components (Classes, Variables, Functions, Class Functions, Properties) in the Code Map panel and popup",
        default=True,
    )

    show_class_type: BoolProperty(
        name="Show Class Type Filter in Panel",
        description="Toggle to display the class type filter in the Code Map panel. Enabling this option will show the filter for class types, such as Classes, Operators, Panels, etc.",
        default=True,
    )

    code_filter_type: EnumProperty(
        name="Code Filter Type",
        items=[
            ("ALL", "All", "Show all code elements"),
            ("PANEL", "Panel", "Show panel-related code elements"),
            ("OPERATOR", "Operator", "Show operator-related code elements"),
            ("UI_LIST", "UiList", "Show UiList-related code elements"),
            ("PROPERTY_GROUP", "PropertyGroup", "Show PropertyGroup-related code elements"),
            ("ADDON_PREFERENCES", "Addon Preferences", "Show Addon Preferences"),
        ],
        default="ALL",
    )

    # Update Checker
    auto_check_update = BoolProperty(
        name="Auto-check for Update",
        description="If enabled, auto-check for updates using an interval",
        default=False)

    updater_interval_months = IntProperty(
        name='Months',
        description="Number of months between checking for updates",
        default=0,
        min=0)

    updater_interval_days = IntProperty(
        name='Days',
        description="Number of days between checking for updates",
        default=7,
        min=0,
        max=31)

    updater_interval_hours = IntProperty(
        name='Hours',
        description="Number of hours between checking for updates",
        default=0,
        min=0,
        max=23)

    updater_interval_minutes = IntProperty(
        name='Minutes',
        description="Number of minutes between checking for updates",
        default=0,
        min=0,
        max=59)

    def draw(self, context):
        layout = self.layout

        # Character Count
        box = layout.box()
        row = box.row()
        row.label(text="Character Count")
        row.prop(self, "enable_character_count", text="")

        # Jump to Line
        box = layout.box()
        row = box.row()
        row.label(text="Jump to Line")
        row.prop(self, "enable_jump_to_line", text="")

        # Trim Whitespace
        box = layout.box()
        row = box.row()
        row.label(text="Trim Whitespace")
        row.prop(self, "enable_trim_whitespace", text="")

        # Code Map
        box = layout.box()
        row = box.row()
        row.label(text="Code Map")
        row.prop(self, "enable_code_map", text="")
        sub_box = box.box()
        sub_box.prop(self, "show_code_filters")
        sub_box.prop(self, "show_class_type")
        sub_box.prop(self, "code_map_category")

        # Find Replace
        box = layout.box()
        row = box.row()
        row.label(text="Find & Replace")
        row.prop(self, "enable_find_replace", text="")
        sub_box = box.box()
        sub_box.prop(self, "enable_find_set_selected")
        sub_box.prop(self, "enable_replace_set_selected")
        sub_box.prop(self, "display_count_label")

        # Open Recent
        box = layout.box()
        row = box.row()
        row.label(text="Open Recent")
        row.prop(self, "enable_open_recent", text="")
        sub_box = box.box()
        sub_box.prop(self, "enable_open_recent_panel")
        sub_box.prop(self, "open_recent_category")

        # Updater settings
        addon_updater_ops.update_settings_ui(self, context)


classes = [Textify_Preferences]


def register():
    addon_updater_ops.register(bl_info)
    
    for cls in classes:
        addon_updater_ops.make_annotations(cls)
        bpy.utils.register_class(cls)
    
    character_count.register()
    code_map.register()
    find_replace.register()
    jump_to_line.register()
    open_recent.register()
    trim_whitespace.register()

    context = bpy.context
    prefs = context.preferences.addons[__package__].preferences
    Textify_Preferences.update_cm_category(prefs, context)
    Textify_Preferences.update_op_category(prefs, context)


def unregister():
    # Addon updater unregister.
    addon_updater_ops.unregister()

    character_count.unregister()
    code_map.unregister()
    find_replace.unregister()
    jump_to_line.unregister()
    open_recent.unregister()
    trim_whitespace.unregister()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
