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
    "version": (1, 1),
    "author": "Jithu",
    "location": "Text Editor > Sidebar",
    "description": "All-in-one tool for enhancing Blender's Text Editor",
    "category": "Text Editor",
    "tracker_url": "https://github.com/Jishnu-jithu/text-editor-addons/issues/new/choose",
}


import bpy
import json
import os
from bpy.types import Operator, AddonPreferences
from bpy.props import BoolProperty, EnumProperty, IntProperty, StringProperty

from . import (
    addon_updater_ops,
    character_count,
    code_map,
    drag_and_drop,
    jump_to_line,
    find_replace,
    trim_whitespace,
    open_recent,
)


class BACKUP_OT_backup_preferences(Operator):
    bl_idname = "backup.backup_preferences"
    bl_label = "Backup Preferences"
    bl_description = "Backup addon preferences to a JSON file"

    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        data = {
            "enable_character_count": prefs.enable_character_count,
            "enable_find_replace": prefs.enable_find_replace,
            "enable_import_script": prefs.enable_import_script,
            "enable_install_script": prefs.enable_install_script,
            "enable_jump_to_line": prefs.enable_jump_to_line,
            "enable_open_recent": prefs.enable_open_recent,
            "enable_code_map": prefs.enable_code_map,
            "enable_trim_whitespace": prefs.enable_trim_whitespace,
            "code_map_category": prefs.code_map_category,
            "open_recent_category": prefs.open_recent_category,
            "display_text_editor_options": prefs.display_text_editor_options,
            "enable_open_recent_panel": prefs.enable_open_recent_panel,
            "display_count_label": prefs.display_count_label,
            "enable_replace_set_selected": prefs.enable_replace_set_selected,
            "enable_find_set_selected": prefs.enable_find_set_selected,
            "auto_check_update": prefs.auto_check_update,
        }

        filepath = os.path.join(os.path.expanduser("~"), "Documents", "textify", "preferences_backup.json")

        # Create the directory if it doesn't exist
        directory = os.path.dirname(filepath)
        os.makedirs(directory, exist_ok=True)

        with open(filepath, 'w') as file:
            json.dump(data, file, indent=4)

        self.report({'INFO'}, f"Preferences backed up to {filepath}")
        return {'FINISHED'}


class RESTORE_OT_restore_preferences(Operator):
    bl_idname = "restore.restore_preferences"
    bl_label = "Restore Preferences"
    bl_description = "Restore addon preferences from a JSON file"

    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences

        filepath = os.path.join(os.path.expanduser("~"), "Documents", "textify", "preferences_backup.json")

        try:
            with open(filepath, 'r') as file:
                data = json.load(file)

            prefs.enable_character_count = data.get("enable_character_count", True)
            prefs.enable_find_replace = data.get("enable_find_replace", True)
            prefs.enable_import_script = data.get("enable_import_script", True)
            prefs.enable_install_script = data.get("enable_install_script", True)
            prefs.enable_jump_to_line = data.get("enable_jump_to_line", True)
            prefs.enable_open_recent = data.get("enable_open_recent", True)
            prefs.enable_code_map = data.get("enable_code_map", True)
            prefs.enable_trim_whitespace = data.get("enable_trim_whitespace", True)
            prefs.code_map_category = data.get("code_map_category", "Code Map")
            prefs.open_recent_category = data.get("open_recent_category", "Text")
            prefs.display_text_editor_options = data.get("display_text_editor_options", True)
            prefs.enable_open_recent_panel = data.get("enable_open_recent_panel", True)
            prefs.display_count_label = data.get("display_count_label", True)
            prefs.enable_replace_set_selected = data.get("enable_replace_set_selected", True)
            prefs.enable_find_set_selected = data.get("enable_find_set_selected", True)
            prefs.auto_check_update = data.get("auto_check_update", True)

            self.report({'INFO'}, f"Preferences restored from {filepath}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to restore preferences: {e}")

        return {'FINISHED'}



@addon_updater_ops.make_annotations
class Textify_Preferences(AddonPreferences):
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

    # Custom panel category
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

    # Enable/Disable features
    enable_character_count = BoolProperty(
        name="Character Count",
        description="Enable or disable the character count",
        default=True
    )

    enable_find_replace = BoolProperty(
        name="Find & Replace",
        description="Enable or disable the Find & Replace",
        default=True
    )

    enable_import_script: BoolProperty(
        name="Drag & Drop Script Import",
        default=False,
        description="Toggle to enable/disable importing of scripts into the text editor using drag and drop",
    )

    enable_install_script: bpy.props.BoolProperty(
        name="Drag & Drop Addon Installation",
        default=True,
        description="Toggle to enable/disable installation of addons using drag and drop",
    )

    enable_jump_to_line = BoolProperty(
        name="Jump to Line",
        description="Enable or disable the Jump to Line",
        default=True
    )

    enable_open_recent = BoolProperty(
        name="Open Recent",
        description="Enable or disable the Open Recent",
        update=open_recent.update_ui,
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

    # Code Map preferences
    show_code_filters: BoolProperty(
        name="Display Code Filters in Panel",
        description="Toggle to display the code components (Classes, Variables, Functions, Class Functions, Properties) in the Code Map panel and popup",
        default=True,
    )

    show_class_type: BoolProperty(
        name="Display Class Type Filter in Panel",
        description="Toggle to display the class type filter in the Code Map panel. Enabling this option will show the filter for class types, such as Classes, Operators, Panels, etc.",
        default=True,
    )

    code_filter_type: EnumProperty(
        name="Code Filter Type",
        items=[
            ("ALL", "All", "Display all code elements"),
            ("PANEL", "Panel", "Display panel-related code elements"),
            ("OPERATOR", "Operator", "Display operator-related code elements"),
            ("UI_LIST", "UiList", "Display UiList-related code elements"),
            ("PROPERTY_GROUP", "PropertyGroup", "Display PropertyGroup-related code elements"),
            ("ADDON_PREFERENCES", "Addon Preferences", "Display Addon Preferences"),
        ],
        default="ALL",
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

    # Open recent preferences
    enable_open_recent_panel = BoolProperty(
        name="Enable Open Recent Panel",
        description="Enable or disable the Open Recent panel",
        default=True
    )

    display_text_editor_options: BoolProperty(
        name="Display Text Editor Controls",
        description="Display or hide advanced options in the UI",
        default=True,
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

        # First Row
        row = layout.row()
        box = row.box()
        box.prop(self, "enable_character_count", text="Character Count")
        box = row.box()
        box.prop(self, "enable_code_map", text="Code Map")

        # Second Row
        if bpy.app.version >= (4, 1, 0):
            row = layout.row()
            box = row.box()
            box.prop(self, "enable_install_script")

            box = row.box()
            box.prop(self, "enable_import_script")

        row = layout.row()
        box = row.box()
        box.prop(self, "enable_find_replace", text="Find & Replace")
        box = row.box()
        box.prop(self, "enable_jump_to_line", text="Jump to Line")

        # Third Row
        row = layout.row()
        box = row.box()
        box.prop(self, "enable_open_recent", text="Open Recent")
        box = row.box()
        box.prop(self, "enable_trim_whitespace", text="Trim Whitespace")

        layout.use_property_split = True
        layout.use_property_decorate = False

        # Preferences of code_map, find_replace and open_recent
        if self.enable_code_map:
            self.draw_settings_code_map(layout)

        if self.enable_find_replace:
            self.draw_settings_find_replace(layout)

        if self.enable_open_recent:
            self.draw_settings_open_recent(layout)

        layout = self.layout
        layout.use_property_split = False

        # Backup Settings
        box = layout.box()
        row = box.row()
        row.label(text="Backup Settings")

        # Backup and Restore Operators in the same row, not aligned
        row = box.row()
        row.scale_y = 1.5
        row.operator("backup.backup_preferences", text="Backup Preferences")
        row.operator("restore.restore_preferences", text="Restore Preferences")

        # Updater settings
        addon_updater_ops.update_settings_ui(self, context)

    def draw_settings_code_map(self, layout):
        box = layout.box()
        row = box.row()

        row.label(text="Code Map Settings")
        box.prop(self, "show_code_filters")
        box.prop(self, "show_class_type")
        box.prop(self, "code_map_category")

    def draw_settings_find_replace(self, layout):
        box = layout.box()
        row = box.row()

        row.label(text="Find & Replace Settings")
        box.prop(self, "enable_find_set_selected")
        box.prop(self, "enable_replace_set_selected")
        box.prop(self, "display_count_label")

    def draw_settings_open_recent(self, layout):
        box = layout.box()
        row = box.row()

        row.label(text="Open Recent Settings")
        box.prop(self, "enable_open_recent_panel")
        box.prop(self, "display_text_editor_options")
        box.prop(self, "open_recent_category")


classes = [BACKUP_OT_backup_preferences, RESTORE_OT_restore_preferences, Textify_Preferences]


def register():
    addon_updater_ops.register(bl_info)

    for cls in classes:
        addon_updater_ops.make_annotations(cls)
        bpy.utils.register_class(cls)

    open_recent.register()
    character_count.register()
    code_map.register()
    drag_and_drop.register()
    find_replace.register()
    trim_whitespace.register()

    jump_to_line.register()

    context = bpy.context
    prefs = context.preferences.addons[__package__].preferences

    open_recent.update_ui(prefs, context)
    print_to_console.update_print(prefs, context)
    Textify_Preferences.update_cm_category(prefs, context)
    Textify_Preferences.update_op_category(prefs, context)


def unregister():
    # Addon updater unregister.
    addon_updater_ops.unregister()

    open_recent.unregister()
    character_count.unregister()
    code_map.unregister()
    drag_and_drop.unregister()
    find_replace.unregister()
    trim_whitespace.unregister()

    jump_to_line.unregister()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
