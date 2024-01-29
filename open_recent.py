# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; version 3
#  of the License.
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
# ##### END GPL LICENSE BLOCK #####


import bpy
import os
import subprocess
import time

from bpy.app.handlers import persistent
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.types import PropertyGroup, Operator, Panel, Menu, UIList
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    IntProperty,
    StringProperty,
    EnumProperty,
    PointerProperty
)


# ---------------------------
#    Function Definitions
# ---------------------------


class TEXT_PG_properties(PropertyGroup):
    recent_list: CollectionProperty(type=PropertyGroup)
    recent_list_index: IntProperty(name="Recent list index")
    display_folder: BoolProperty(name="Filter __init__.py file", description="Display Folder Name for __init__.py files", default=True)


def get_recent_list():
    scene = bpy.context.scene
    props = scene.recent_list_props
    if hasattr(scene, 'recent_list_props'):
        list = props.recent_list
        index = props.recent_list_index
    else:
        list = []
        index = 0
    txt_path = os.path.join(os.path.expanduser("~/Documents/Open Recent"), "open_recent.txt")
    return list, index, txt_path


def update_list():
    list, index, txt_path = get_recent_list()
    props = bpy.context.scene.recent_list_props

    if os.path.exists(txt_path):
        # Read the file and get the unique paths
        with open(txt_path, 'r') as txt_file:
            lines = txt_file.readlines()
            valid_paths = sorted(set(lines), key=lines.index)

        # Clear the UI list
        props.recent_list.clear()

        # Add the unique paths back to the UI list
        for line in valid_paths:
            props.recent_list.add().name = line.strip()


# --------------------------
#         Operators
# --------------------------


class TEXT_OT_open_mainfile(Operator, ImportHelper):
    bl_idname = "text.open_mainfile"
    bl_label = "Open Text"
    bl_description = "Open a new text data-block"
    bl_options = {'REGISTER', 'UNDO'}

    # Enable selection of multiple files
    files: CollectionProperty(type=PropertyGroup)
    directory: StringProperty(subtype='DIR_PATH')

    filter_python: BoolProperty(default=True, options={'HIDDEN'})
    filter_folder: BoolProperty(default=True, options={'HIDDEN'})
    hide_props_region: BoolProperty(default=True, options={'HIDDEN'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        list, index, txt_path = get_recent_list()

        for file in self.files:
            filepath = os.path.join(self.directory, file.name)

            # Try to read the file
            try:
                with open(filepath, 'r') as f:
                    file_data = f.read()
            except Exception as e:
                self.report(
                    {'ERROR'},
                    f"Could not open file \"{filepath}\": {str(e)}")
                continue

            bpy.ops.text.open(filepath=filepath)

            imported_files = []
            if os.path.exists(txt_path):
                with open(txt_path, 'r') as txt_file:
                    imported_files = [filepath.strip() for filepath in txt_file.readlines()]

            # Loop over all selected files
            for file in self.files:
                filepath = os.path.join(self.directory, file.name)

                # Remove the file if it's already in the list
                imported_files = [existing_filepath for existing_filepath in imported_files if existing_filepath != filepath]

                # Add the file to the top of the list
                imported_files.insert(0, filepath)

            # Write the updated list back to the file
            with open(txt_path, 'w') as txt_file:
                for filepath in imported_files:
                    txt_file.write(filepath + '\n')

        # Update the UIList
        update_list()
        return {'FINISHED'}


class TEXT_OT_open_file(Operator):
    bl_idname = "text.open_file"
    bl_label = "Open Text"
    bl_description = "Open Text"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty()

    @classmethod
    def description(cls, context, properties):
        if properties.filepath != '':
            try:
                # Get the modified time of the file if it exists
                modified_time = time.strftime("%d %b %Y %I:%M %p", time.localtime(os.path.getatime(properties.filepath)))
                return f"{properties.filepath}\n\nModified: {modified_time}"
            except FileNotFoundError:
                return f"File not found: {properties.filepath}"
            except Exception as e:
                return f"Error retrieving file information: {str(e)}"
        else:
            return "Open Text"

    def execute(self, context):
        list, index, txt_path = get_recent_list()

        # Check if the file exists
        if not os.path.isfile(self.filepath):
            self.report({'WARNING'}, f"Cannot read file \"{self.filepath}\": No such file or directory.")
            self.remove_invalid_file_from_txt_file()
            return {'CANCELLED'}

        # Check if the file is already open
        for text in bpy.data.texts:
            if text.filepath == self.filepath:
                # The file is already open, so make it the active text block
                context.space_data.text = text
                break
        else:
            # The file is not open, so open it
            bpy.ops.text.open(filepath=self.filepath)

        imported_files = []
        if os.path.exists(txt_path):
            with open(txt_path, 'r') as txt_file:
                imported_files = [filepath.strip() for filepath in txt_file.readlines()]

        imported_files = [filepath for filepath in imported_files if filepath != self.filepath]

        imported_files.insert(0, self.filepath)
        with open(txt_path, 'w') as txt_file:
            for filepath in imported_files:
                txt_file.write(filepath + '\n')

        update_list()
        return {'FINISHED'}

    def remove_invalid_file_from_txt_file(self):
        list, index, txt_path = get_recent_list()

        if os.path.exists(txt_path):
            with open(txt_path, 'r') as txt_file:
                imported_files = [filepath.strip() for filepath in txt_file.readlines()]
            imported_files = [filepath for filepath in imported_files if filepath != self.filepath]
            with open(txt_path, 'w') as txt_file:
                for filepath in imported_files:
                    txt_file.write(filepath + '\n')


class TEXT_OT_save_mainfile(Operator, ExportHelper):
    bl_idname = "text.save_mainfile"
    bl_label = "Save"
    bl_description = "Save active text data-block"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".py"
    filter_glob: StringProperty(default="*.py", options={'HIDDEN'})

    def invoke(self, context, event):
        st = context.space_data.text

        # Check if the filepath ends with '.py'
        if not st.name.endswith('.py'):
            self.filepath = st.name + '.py'
        else:
            self.filepath = st.name

        if not st.is_in_memory:
            bpy.ops.text.save()
            self.report({'INFO'}, f"Saved text {st.filepath}")
            return {'CANCELLED'}

        return super().invoke(context, event)

    def execute(self, context):
        st = context.space_data.text
        list, index, txt_path = get_recent_list()

        bpy.ops.text.save_as(filepath=self.filepath, check_existing=True)

        # Load existing file paths from 'open_recent.txt' if it exists
        imported_files = []
        if os.path.exists(txt_path):
            with open(txt_path, 'r') as txt_file:
                imported_files = [filepath.strip() for filepath in txt_file.readlines()]

        st_filepath = st.filepath
        if st_filepath in imported_files:
            imported_files.remove(st_filepath)

        imported_files.insert(0, st_filepath)

        with open(txt_path, 'w') as txt_file:
            for filepath in imported_files:
                txt_file.write(filepath + '\n')

        update_list()
        return {'FINISHED'}


class TEXT_OT_save_as_mainfile(Operator, ExportHelper):
    bl_idname = "text.save_as_mainfile"
    bl_label = "Save As"
    bl_description = "Save active text data-block"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".py"
    filter_glob: StringProperty(default="*.py", options={'HIDDEN'})

    def invoke(self, context, event):
        st = context.space_data.text

        if not st.name.endswith('.py'):
            self.filepath = st.name + '.py'
        else:
            self.filepath = st.name

        return super().invoke(context, event)

    def execute(self, context):
        st = context.space_data.text
        list, index, txt_path = get_recent_list()

        bpy.ops.text.save_as(filepath=self.filepath, check_existing=True)

        if not st.filepath:
            self.report({'WARNING'}, "No valid text data-block to save")
            return {'CANCELLED'}

        imported_files = []
        if os.path.exists(txt_path):
            with open(txt_path, 'r') as txt_file:
                imported_files = [filepath.strip() for filepath in txt_file.readlines()]

        st_filepath = st.filepath
        if st_filepath in imported_files:
            imported_files.remove(st_filepath)

        imported_files.insert(0, st_filepath)

        with open(txt_path, 'w') as txt_file:
            for filepath in imported_files:
                txt_file.write(filepath + '\n')

        update_list()
        return {'FINISHED'}


class TEXT_OT_clear_recent(Operator):
    """Operator for deleting a preset."""

    bl_idname = "text.clear_recent"
    bl_label = "Remove All" if bpy.app.version >= (4, 1, 0) else "Clear Recent Files List"
    bl_description = "Clear the recent files list"
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        # Save the original position of the mouse
        self.first_mouse_x = event.mouse_x
        self.first_mouse_y = event.mouse_y

        # Warp the mouse to some xy coords
        context.window.cursor_warp(int((context.window.width / 2) + 60), int((context.window.height / 2) + 15))

        # Invoke popup
        wm = context.window_manager
        result = wm.invoke_props_dialog(self, width=300)

        # Warp the mouse back to the original position
        context.window.cursor_warp(self.first_mouse_x, self.first_mouse_y)

        return result

    def draw(self, context):
        layout = self.layout
        layout.label(text="Remove all items from the recent files list")

    def execute(self, context):
        list, index, txt_path = get_recent_list()

        with open(txt_path, 'w') as txt_file:
            txt_file.write('')

        update_list()
        return {'FINISHED'}


class TEXT_OT_open_recent_actions(Operator):
    bl_idname = "text.recent_actions"
    bl_label = ""
    bl_description = "Open Recent actions"
    bl_options = {'REGISTER', 'UNDO'}


    action: EnumProperty(items=[
        ('ADD', 'Add', ''),
        ('REMOVE', 'Remove', ''),
        ('MOVE_UP', 'Move Up', ''),
        ('MOVE_DOWN', 'Move Down', ''),
        ('OPEN_SELECTED', 'Open Selected', ''),
        ('RECENT_CLEANUP', 'Recent Cleanup', ''),
        ('REMOVE_DUPLICATES', 'Remove Duplicates', ''),
        ('OPEN_FOLDER', 'Open File Location', ''),
    ])


    @classmethod
    def poll(cls, context):
        return context.scene.recent_list_props.recent_list


    @classmethod
    def description(cls, context, properties):
        descriptions = {
            'ADD': 'Add the current file to the list',
            'REMOVE': 'Remove the selected file from the list',
            'MOVE_UP': 'Move Up',
            'MOVE_DOWN': 'Move Down',
            'OPEN_SELECTED': 'Open the selected file',
            'RECENT_CLEANUP': 'Remove all invalid files from the list.\n\nMissing path: {missing}',
            'REMOVE_DUPLICATES': 'Remove duplicate items from the list.\n\nDuplicate path: {duplicates}',
            'OPEN_FOLDER': 'Open the folder of the selected file in Windows Explorer.\n\n{filepath}',
        }

        # Custom descriptions for RECENT_CLEANUP, REMOVE_DUPLICATES, and OPEN_FOLDER
        if properties.action in ['RECENT_CLEANUP', 'REMOVE_DUPLICATES', 'OPEN_FOLDER']:
            list, index, _ = get_recent_list()  # Include the index here

            if properties.action == 'RECENT_CLEANUP':
                valid_paths = [item.name for item in list if os.path.isfile(item.name)]
                missing_paths = set(item.name for item in list) - set(valid_paths)
                return descriptions.get(properties.action).format(missing=', '.join(missing_paths))

            elif properties.action == 'REMOVE_DUPLICATES':
                valid_paths = [item.name for item in list if os.path.isfile(item.name)]
                seen_paths = set()
                duplicates = [path for path in valid_paths if path in seen_paths or seen_paths.add(path)]
                return descriptions.get(properties.action).format(duplicates=', '.join(duplicates))

            elif properties.action == 'OPEN_FOLDER':
                selected_item = list[index].name
                return descriptions.get(properties.action).format(filepath=selected_item)

        # Default description
        return descriptions.get(properties.action, 'Manage Open Recent List')


    def execute(self, context):
        if self.action == 'ADD':
            return self.add_path(context)
        elif self.action == 'REMOVE':
            return self.remove_path(context)
        elif self.action == 'MOVE_UP':
            return self.move_path(context, 'UP')
        elif self.action == 'MOVE_DOWN':
            return self.move_path(context, 'DOWN')
        elif self.action == 'OPEN_SELECTED':
            return self.open_selected(context)
        elif self.action == 'RECENT_CLEANUP':
            return self.recent_cleanup(context)
        elif self.action == 'REMOVE_DUPLICATES':
            return self.remove_duplicates(context)
        elif self.action == 'OPEN_FOLDER':
            return self.open_folder(context)


    def add_path(self, context):
        st = context.space_data.text
        props = context.scene.recent_list_props

        if st is None:
            self.report({'WARNING'}, "No active text data-block")
            return {'CANCELLED'}

        self.filepath = st.filepath

        # Add the file path to the UI list
        new_item = props.recent_list.add()
        new_item.name = self.filepath
        props.recent_list.move(len(props.recent_list)-1, 0)
        props.recent_list_index = 0

        txt_path = os.path.join(os.path.expanduser("~/Documents/Open Recent"), "open_recent.txt")
        imported_files = []

        if os.path.exists(txt_path):
            with open(txt_path, 'r') as txt_file:
                imported_files = [filepath.strip() for filepath in txt_file.readlines()]

        imported_files.insert(0, self.filepath)
        with open(txt_path, 'w') as txt_file:
            for filepath in imported_files:
                txt_file.write(filepath + '\n')

        return {'FINISHED'}


    def remove_path(self, context):
        list, index, txt_path = get_recent_list()
        props = context.scene.recent_list_props

        # Get the path to be removed
        path_to_remove = list[index].name
        list.remove(index)

        if index > 0:
            props.recent_list_index = index - 1

        if os.path.exists(txt_path):
            with open(txt_path, 'r') as txt_file:
                lines = txt_file.readlines()
            with open(txt_path, 'w') as txt_file:
                for line in lines:
                    if line.strip() != path_to_remove:
                        txt_file.write(line)

        return {'FINISHED'}


    def move_path(self, context, direction):
        list, index, txt_path = get_recent_list()
        props = context.scene.recent_list_props

        if self.action == 'MOVE_UP' and index > 0:
            list.move(index, index - 1)
            props.recent_list_index = index - 1

            # Move the corresponding item up in open_recent.txt
            self.move_item_in_file(index, index - 1)

        elif self.action == 'MOVE_DOWN' and index < len(list) - 1:
            list.move(index, index + 1)
            props.recent_list_index = index + 1

            # Move the corresponding item up in open_recent.txt
            self.move_item_in_file(index, index + 1)

        return {'FINISHED'}


    def move_item_in_file(self, from_index, to_index):
        list, index, txt_path = get_recent_list()

        if os.path.exists(txt_path):
            with open(txt_path, 'r') as txt_file:
                imported_files = [line.strip() for line in txt_file.readlines()]

            imported_files.insert(to_index, imported_files.pop(from_index))

            with open(txt_path, 'w') as txt_file:
                for filepath in imported_files:
                    txt_file.write(filepath + '\n')


    def open_selected(self, context):
        props = context.scene.recent_list_props
        index = props.recent_list_index
        selected_item = props.recent_list[index]
        filepath = selected_item.name

        if os.path.exists(filepath):
            bpy.ops.text.open(filepath=filepath)

            # Move the selected item to the top of the list
            props.recent_list.move(index, 0)
            props.recent_list_index = 0

            # Move the corresponding item in open_recent.txt
            self.move_item_in_file(index, 0)
        else:
            self.report({'WARNING'}, f"File not found: {filepath}")

        return {'FINISHED'}


    def recent_cleanup(self, context):
        list, index, txt_path = get_recent_list()
        props = context.scene.recent_list_props

        valid_paths = [item.name for item in list if os.path.isfile(item.name)]
        missing_paths = set(item.name for item in list) - set(valid_paths)

        if missing_paths:
            list.clear()

            # Add the valid file paths back to the UI list
            for path in valid_paths:
                list.add().name = path

            if index >= len(list):
                props.recent_list_index = len(list) - 1

            txt_path = os.path.join(os.path.expanduser("~/Documents/Open Recent"), "open_recent.txt")
            with open(txt_path, 'w') as txt_file:
                for filepath in valid_paths:
                    txt_file.write(filepath + '\n')

            self.report({'INFO'}, f"Cleared missing paths: {', '.join(missing_paths)}")
        return {'FINISHED'}


    def remove_duplicates(self, context):
        list, index, txt_path = get_recent_list()

        # Create a list of unique file paths while preserving the order
        valid_paths = []
        seen_paths = set()

        for item in list:
            path = item.name
            if path not in seen_paths:
                valid_paths.append(path)
                seen_paths.add(path)

        list.clear()

        # Add the unique file paths back to the UI list
        for path in valid_paths:
            list.add().name = path

        if index >= len(list):
            props.recent_list_index = len(list) - 1

        with open(txt_path, 'w') as txt_file:
            for filepath in valid_paths:
                txt_file.write(filepath + '\n')

        self.report({'INFO'}, f"Removed duplicate paths")
        return {'FINISHED'}


    def open_folder(self, context):
        list, index, _ = get_recent_list()
        selected_item = list[index].name

        # Open the folder in Windows Explorer
        folder_path = os.path.dirname(selected_item)
        subprocess.Popen(['explorer', folder_path], shell=True)
        return {'FINISHED'}


# -------------------------
#           Menu
# -------------------------


class TEXT_MT_open_recent(Menu):
    bl_idname = "TEXT_MT_open_recent"
    bl_label = "Open Recent"
    bl_options = {'SEARCH_ON_KEY_PRESS'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.recent_list_props
        list, index, txt_path = get_recent_list()

        valid_paths = [item.name for item in list if os.path.isfile(item.name)]
        missing_paths = set(item.name for item in list) - set(valid_paths)

        imported_files = []
        if os.path.exists(txt_path):
            with open(txt_path, 'r') as txt_file:
                imported_files = txt_file.readlines()

        for filepath in imported_files:
            filepath = filepath.strip()

            # Display the folder name if the file ends with '__init__.py'
            display_name = os.path.basename(filepath)

            if props.display_folder and display_name.lower().endswith('__init__.py'):
                folder_name = os.path.basename(os.path.dirname(filepath))
                display_name = folder_name.lower().replace(" ", "_") + ".py"

            elif props.display_folder:
                display_name = display_name.lower().replace(" ", "_")

                # Ensure it ends with ".py" if it doesn't already
                if not display_name.endswith(".py"):
                    display_name += ".py"

            operator = layout.operator("text.open_file", text=display_name, icon="WORDWRAP_ON")
            if operator:
                operator.filepath = filepath

        if len(imported_files) == 0:
            layout.label(text="No Recent Files")
        else:
            layout.separator()
            if missing_paths:
                layout.operator("text.recent_actions", icon='PANEL_CLOSE', text="Clear Missing Paths").action = 'RECENT_CLEANUP'
            else:
                layout.operator("text.clear_recent", icon="TRASH", text="Clear Recent Files List")


class TEXT_MT_cleanup_menu(Menu):
    bl_idname = "TEXT_MT_cleanup_menu"
    bl_label = "Cleanup Menu"

    def draw(self, context):
        layout = self.layout
        list, index, txt_path = get_recent_list()

        valid_paths = [item.name for item in list if os.path.isfile(item.name)]
        missing_paths = set(item.name for item in list) - set(valid_paths)

        row = layout.row()
        if missing_paths:
            row.operator("text.recent_actions", icon='PANEL_CLOSE', text="Clear Missing Paths").action = 'RECENT_CLEANUP'

        layout.separator()
        layout.operator("text.clear_recent", icon="TRASH", text="Clear Recent Files List")

        # Check if there are any duplicate items in the list
        if len(list) != len(set(item.name for item in list)):
            layout.separator()
            layout.operator("text.recent_actions", icon="DUPLICATE", text="Clear Duplicates").action = 'REMOVE_DUPLICATES'


# --------------------------
#           UIList
# --------------------------


class TEXT_UL_open_recent(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # Display the folder name if the file ends with '__init__.py'
        display_name = os.path.basename(item.name)
        props = context.scene.recent_list_props

        if props.display_folder and display_name.lower().endswith('__init__.py'):
            folder_name = os.path.basename(os.path.dirname(item.name))
            display_name = folder_name.lower().replace(" ", "_") + ".py"
        elif props.display_folder:
            display_name = display_name.lower().replace(" ", "_")

            if not display_name.endswith(".py"):
                display_name += ".py"

        layout.label(text=display_name, icon='WORDWRAP_ON')


# ---------------------------
#           Panel
# ---------------------------


class TEXT_PT_open_recent(Panel):
    bl_label = "Open Recent"
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Text"

    @classmethod
    def poll(cls, context):
        prefs = bpy.context.preferences.addons[__package__].preferences
        return prefs.enable_open_recent_panel

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.recent_list_props
        st = context.space_data
        text = st.text

        row = layout.row()
        row.template_list("TEXT_UL_open_recent", "", props, "recent_list", props, "recent_list_index", rows=8)

        col = row.column(align=True)
        col.scale_y = 1.1
        if text and not any(item.name == text.filepath for item in props.recent_list) and not text.is_in_memory:
            sub = col.column(align=True)
            sub.operator("text.recent_actions", icon='ADD', text="").action = 'ADD'
        else:
            sub = col.column(align=True)
            sub.operator("text.recent_actions", icon='ADD', text="").action = 'ADD'
            sub.enabled = False

        col.operator("text.recent_actions", icon='REMOVE', text="").action = 'REMOVE'
        col.separator()

        col.menu("TEXT_MT_cleanup_menu", icon='DOWNARROW_HLT', text="")
        col.separator()

        col.operator("text.recent_actions", icon='TRIA_UP', text="").action = 'MOVE_UP'
        col.operator("text.recent_actions", icon='TRIA_DOWN', text="").action = 'MOVE_DOWN'
        col.separator()

        col.operator("text.recent_actions", icon='FOLDER_REDIRECT', text="").action = 'OPEN_FOLDER'
        col.separator()

        if props.recent_list:
            col.prop(props, "display_folder", text="", icon="FILTER", toggle=True)
        else:
            col.enabled = False
            col.prop(props, "display_folder", text="", icon="FILTER", toggle=True)

        layout.operator("text.recent_actions", text="Open Selected").action = 'OPEN_SELECTED'


# ----------------------------
#       Draw Custom Menu
# ----------------------------


# Store a reference to the original draw method
editor_header = bpy.types.TEXT_HT_header.draw
editor_menu = bpy.types.TEXT_MT_text.draw


def recent_header(self, context):
    layout = self.layout

    st = context.space_data
    text = st.text
    is_syntax_highlight_supported = st.is_syntax_highlight_supported()
    layout.template_header()

    TEXT_MT_editor_menus.draw_collapsible(context, layout)

    layout.separator_spacer()

    if text and text.is_modified:
        row = layout.row(align=True)
        row.alert = True
        row.operator("text.resolve_conflict", text="", icon='QUESTION')

    if text:
        row = layout.row(align=True)
        row.template_ID(st, "text", new="text.new", unlink="text.unlink", open="text.open_mainfile")

        is_osl = text.name.endswith((".osl", ".osl"))
        if is_osl:
            row.operator("node.shader_script_update",
                         text="", icon='FILE_REFRESH')
        else:
            row = layout.row()
            row.active = is_syntax_highlight_supported
            row.operator("text.run_script", text="", icon='PLAY')
    else:
        row = layout.row(align=True)
        row.template_ID(st, "text", new="text.new",
                    unlink="text.unlink", open="text.open_mainfile")

    layout.separator_spacer()


    row = layout.row(align=True)
    row.prop(st, "show_line_numbers", text="")
    row.prop(st, "show_word_wrap", text="")

    syntax = row.row(align=True)
    syntax.active = is_syntax_highlight_supported
    syntax.prop(st, "show_syntax_highlight", text="")


def recent_text_menu(self, context):
    layout = self.layout
    scene = context.scene
    st = context.space_data
    text = st.text

    list, index, txt_path = get_recent_list()

    layout.operator("text.new", text="New", icon='FILE_NEW')

    layout.operator("text.open_mainfile", text="Open...", icon='FILE_FOLDER')
    prefs = bpy.context.preferences.addons[__package__].preferences

    if prefs.enable_open_recent:
        imported_files = []
        if os.path.exists(txt_path):
            with open(txt_path, 'r') as txt_file:
                imported_files = txt_file.readlines()

        if len(imported_files) > 0:
            layout.menu("TEXT_MT_open_recent")
        else:
            row = layout.row()
            row.enabled = False
            row.menu("TEXT_MT_open_recent")

    if text:
        layout.separator()
        row = layout.row()
        row.operator("text.reload")
        row.enabled = not text.is_in_memory

        row = layout.row()
        row.operator("text.jump_to_file_at_point", text="Edit Externally")
        row.enabled = (not text.is_in_memory and context.preferences.filepaths.text_editor != "")

        layout.separator()
        layout.operator("text.save_mainfile", icon='FILE_TICK')
        layout.operator("text.save_as_mainfile", text="Save As...           ")

        layout.separator()

        row = layout.row()
        row.operator("text.make_internal")
        row.enabled = not text.is_in_memory

        layout.separator()
        layout.prop(text, "use_module")
        layout.prop(st, "use_live_edit")
        layout.separator()
        layout.operator("text.run_script")


class TEXT_MT_editor_menus(Menu):
    bl_idname = "TEXT_MT_editor_menus"
    bl_label = ""

    def draw(self, context):
        layout = self.layout
        st = context.space_data
        text = st.text

        layout.menu("TEXT_MT_view")
        layout.menu("TEXT_MT_text")

        if text:
            layout.menu("TEXT_MT_edit")
            layout.menu("TEXT_MT_select")
            layout.menu("TEXT_MT_format")

        layout.menu("TEXT_MT_templates")


# ================================================================================ #


# Load UIList On Startup
@persistent
def load_list(dummy):
    prefs = bpy.context.preferences.addons[__package__].preferences

    if prefs.enable_open_recent:
        list, index, txt_path = get_recent_list()
        props = bpy.context.scene.recent_list_props

        if os.path.exists(txt_path):
            # Read the file and get the valid paths
            with open(txt_path, 'r') as txt_file:
                lines = txt_file.readlines()
                valid_paths = sorted(set(lines), key=lines.index)

            # Clear the UI list
            props.recent_list.clear()

            # Add the valid paths back to the UI list
            for line in valid_paths:
                props.recent_list.add().name = line.strip()


# ================================================================================ #


classes = (
    TEXT_PG_properties,

    TEXT_OT_open_mainfile,
    TEXT_OT_open_file,
    TEXT_OT_save_mainfile,
    TEXT_OT_save_as_mainfile,

    TEXT_MT_open_recent,
    TEXT_MT_cleanup_menu,

    TEXT_UL_open_recent,
    #TEXT_PT_open_recent,
    TEXT_OT_clear_recent,
    TEXT_OT_open_recent_actions,
)


addon_keymaps = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.app.timers.register(lambda: load_list(None))

    bpy.types.TEXT_HT_header.draw = recent_header
    bpy.types.TEXT_MT_text.draw = recent_text_menu

    if not hasattr(bpy.types, 'TEXT_MT_editor_menus'):
        bpy.utils.register_class(TEXT_MT_editor_menus)

    bpy.types.Scene.recent_list_props = PointerProperty(type=TEXT_PG_properties)

    bpy.app.handlers.load_post.append(load_list)

    # handle the keymap
    wm = bpy.context.window_manager

    if wm.keyconfigs.addon:
        km = wm.keyconfigs.addon.keymaps.new(name='Text', space_type='TEXT_EDITOR')

        kmi = km.keymap_items.new('text.open_mainfile', 'O', 'PRESS', ctrl=True, shift=False)
        addon_keymaps.append((km, kmi))

        kmi = km.keymap_items.new('text.save_mainfile', 'S', 'PRESS', ctrl=True, shift=False)
        addon_keymaps.append((km, kmi))

        kmi = km.keymap_items.new('text.save_as_mainfile', 'S', 'PRESS', ctrl=True, shift=True)
        addon_keymaps.append((km, kmi))

        kmi = km.keymap_items.new('wm.call_menu', 'O', 'PRESS', ctrl=True, shift=True)
        kmi.properties.name = "TEXT_MT_open_recent"
        addon_keymaps.append((km, kmi))


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.TEXT_HT_header.draw = editor_header # Load original header
    bpy.types.TEXT_MT_text.draw = editor_menu # Load original menu

    # Remove the properties
    del bpy.types.Scene.recent_list_props

    # Remove the keymaps
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    bpy.app.handlers.load_post.remove(load_list)

    bpy.utils.unregister_class(TEXT_PT_open_recent)
    
