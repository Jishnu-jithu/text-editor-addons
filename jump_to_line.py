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

bl_info = {
    "name": "Jump to line",
    "author": "Jishnu jithu",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "Text editor > Sidebar > Go to line",
    "description": "Go to line",
    "doc_url": "",
    "category": "Scripting",
}

def update_line_number(self, context):
    text_editor = context.space_data.text
    if text_editor is not None:
        lines = text_editor.as_string().split('\n')

        line_number = context.scene.line_number
        if line_number > 0:
            # Calculate the maximum line number based on the actual number of lines in the script
            max_line_number = len(lines)
            if line_number > max_line_number:
                line_number = max_line_number
                context.scene.line_number = line_number

            bpy.ops.text.jump(line=line_number)

def draw_func(self, context):
    layout = self.layout
    row = layout.row(align=True)
    row.scale_x = .9
            
    if context.space_data.text is not None:        
        row.prop(context.scene, "line_number", text="Line")

def register():
    bpy.types.TEXT_HT_header.append(draw_func)
    
    bpy.types.Scene.line_number = bpy.props.IntProperty(min=1, update=update_line_number)

def unregister():    
    bpy.types.TEXT_HT_header.remove(draw_func)
    
    del bpy.types.Scene.line_number

if __name__ == "__main__":
    register()
