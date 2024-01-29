# ##### BEGIN GPL LICENSE BLOCK #####
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
# ##### END GPL LICENSE BLOCK #####


import bpy

from bpy.types import Operator


# ------------------------------


class TEXT_OT_find_previous(Operator):
    bl_idname = "text.find_previous"
    bl_label = "Find Previous"

    def execute(self, context):
        text_data = bpy.context.edit_text

        if text_data is not None:
            cursor_line = text_data.current_line_index
            cursor_character = text_data.current_character
            find = bpy.context.space_data.find_text

            lines_displayed = bpy.context.area.height // 16

            # Start the search from the cursor position
            found = self.search_from_cursor(text_data, cursor_line, cursor_character, find, lines_displayed)

            # If the word was not found, start the search from the bottom of the text
            if not found:
                found = self.search_from_bottom(text_data, cursor_line, find, lines_displayed)

            if not found:
                self.report({'WARNING'}, "Text not found: {}".format(find))

        return {'FINISHED'}

    def search_from_cursor(self, text_data, cursor_line, cursor_character, find_text, lines_displayed):
        for i in range(cursor_line, -1, -1):
            line = text_data.lines[i].body
            line = line[:cursor_character] if i == cursor_line else line

            if not bpy.context.space_data.use_match_case:
                line = line.lower()
                find_text = find_text.lower()

            index = line.rfind(find_text)

            if index != -1:
                self.update_text_data(text_data, i, index, find_text, lines_displayed)
                return True

        return False

    def search_from_bottom(self, text_data, cursor_line, find_text, lines_displayed):
        for i in range(len(text_data.lines) - 1, cursor_line, -1):
            line = text_data.lines[i].body

            if not bpy.context.space_data.use_match_case:
                line = line.lower()
                find_text = find_text.lower()

            index = line.rfind(find_text)

            if index != -1:
                self.update_text_data(text_data, i, index, find_text, lines_displayed)
                return True

        return False

    def update_text_data(self, text_data, line_index, character_index, find_text, lines_displayed):
        text_data.current_line_index = line_index
        text_data.current_character = character_index + len(find_text)
        text_data.select_set(line_index, character_index, line_index, character_index + len(find_text))

        if line_index < bpy.context.space_data.top or line_index > bpy.context.space_data.top + lines_displayed:
            bpy.context.space_data.top = max(0, line_index - lines_displayed // 2)

        # Extract the found word from the original line
        found_word = text_data.lines[line_index].body[character_index:character_index + len(find_text)]

    def report_warning(self, message):
        self.report({'WARNING'}, message)

        return {'FINISHED'}


# ------------------------------


class TEXT_OT_find_replace(Operator):
    bl_idname = "text.find_replace"
    bl_label = "Find & Replace"

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        st = context.space_data
        prefs = bpy.context.preferences.addons[__package__].preferences

        # Check the settings before calling the operators
        if prefs.enable_find_set_selected:
            bpy.ops.text.find_set_selected()

        if prefs.enable_replace_set_selected:
            bpy.ops.text.replace_set_selected()

        bpy.ops.text.find_previous()

        max_line_length = 54
        if (len(st.find_text) > max_line_length or len(st.replace_text) > max_line_length):
            width=430
        else:
            width=360

        return context.window_manager.invoke_popup(self, width=width)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        st = context.space_data
        find = st.find_text

        row = layout.row()
        row.label(text="Find and Replace", icon="ZOOM_ALL")
        col = row.column()
        col.alignment = 'CENTER'

        if find:
            self.display_word_count(context, col, find)

        self.draw_settings(st, scene, layout)
        self.draw_find_repalce(st, scene, layout)

    def draw_settings(self, st, scene, layout):
        row = layout.row(align=True)
        row.prop(st, "use_match_case", text="Case", toggle=True)
        row.prop(st, "use_find_wrap", text="Wrap", toggle=True)
        row.prop(st, "use_find_all", text="All", toggle=True)
        layout.separator()

    def draw_find_repalce(self, st, scene, layout):
        row = layout.row(align=True)
        row.prop(st, "find_text", icon='VIEWZOOM', text="")
        row.scale_x = 1.1
        row.operator("text.find", text="", icon="SORT_ASC")
        row.operator("text.find_previous", text="", icon="SORT_DESC")

        row = layout.row(align=True)
        row.prop(st, "replace_text", icon='DECORATE_OVERRIDE', text="")
        row.scale_x = 1.1
        row.operator("text.replace", text="", icon="ARROW_LEFTRIGHT")
        row.operator("text.replace", text="", icon="ANIM").all = True

    def display_word_count(self, context, col, find):
        text = context.space_data.text
        text_data = context.edit_text
        prefs = bpy.context.preferences.addons[__package__].preferences

        total_count, find_count = self.count_occurrences(text, text_data, find)

        if prefs.display_count_label:
            if find_count == 0 and total_count == 0:
                col.label(text="No matches found")
            else:
                col.label(text=f"{find_count} of {total_count}")

    def count_occurrences(self, text, text_data, find):
        total_count = 0
        find_count = 0

        for i, line in enumerate(text_data.lines):
            line_body = line.body
            find_text = find

            if not bpy.context.space_data.use_match_case:
                line_body = line.body.lower()
                find_text = find.lower()

            line_occurrences = line_body.count(find_text)
            total_count += line_occurrences

            if i == text_data.current_line_index:
                find_count += line_body[:text_data.select_end_character].count(find_text)
            elif i < text_data.current_line_index:
                find_count += line_occurrences

        return total_count, find_count


# ------------------------------


def draw_func(self, context):
    layout = self.layout
    prefs = bpy.context.preferences.addons[__package__].preferences

    if prefs.enable_find_replace:
        layout.operator("text.find_replace", text="Find & Replace Popup")


# ------------------------------


classes = [
    TEXT_OT_find_previous,
    TEXT_OT_find_replace,
]


addon_keymaps = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TEXT_MT_edit.append(draw_func)

    # handle the keymap
    wm = bpy.context.window_manager

    if wm.keyconfigs.addon:
        km = wm.keyconfigs.addon.keymaps.new(name='Text', space_type='TEXT_EDITOR')

        kmi = km.keymap_items.new('text.find_replace', 'F1', 'PRESS')
        addon_keymaps.append((km, kmi))

        # Keymap for find_replace (find previous)
        kmi = km.keymap_items.new('text.find_previous', 'UP_ARROW', 'PRESS', alt=True)
        addon_keymaps.append((km, kmi))

        # Keymap for find (find next)
        kmi = km.keymap_items.new('text.find', 'DOWN_ARROW', 'PRESS', alt=True)
        addon_keymaps.append((km, kmi))


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.TEXT_MT_edit.remove(draw_func)

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
