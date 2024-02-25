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
import os
import ast

from bpy.utils import previews
from bpy.types import Operator, Panel, PropertyGroup, WindowManager
from bpy.props import CollectionProperty, StringProperty, IntProperty, BoolProperty, EnumProperty, PointerProperty


# -------------------------------------------------------------
#                            Icon
# -------------------------------------------------------------


custom_icons = None


def load_icons():
    global custom_icons
    if custom_icons is None:
        custom_icons = previews.new()

    addon_dir = os.path.dirname(os.path.realpath(__file__))

    icons = {
        "class": os.path.join(addon_dir, "icons", "class.png"),
        "function": os.path.join(addon_dir, "icons", "function.png"),
        "method": os.path.join(addon_dir, "icons", "method.png"),
        "property": os.path.join(addon_dir, "icons", "property.png"),
        "variable": os.path.join(addon_dir, "icons", "variable.png")
    }

    for icon_name, icon_path in icons.items():
        if icon_name not in custom_icons:
            custom_icons.load(icon_name, icon_path, 'IMAGE')


def unload_icons():
    global custom_icons
    if custom_icons:
        previews.remove(custom_icons)
        custom_icons = None


# -------------------------------------------------------------
#                          Operators
# -------------------------------------------------------------


class CODE_MAP_OT_jump(Operator):
    bl_idname = "code_map.jump"
    bl_label = "Jump to Line"

    line_number: IntProperty()

    @classmethod
    def description(cls, context, properties):
        return "Jump to line {}".format(properties.line_number)

    def execute(self, context):
        bpy.ops.text.jump(line=self.line_number)
        return {'FINISHED'}


class CODE_MAP_OT_dynamic_toggle(Operator):
    bl_idname = "code_map.toggle_string"
    bl_label = "Show functions and properties"
    bl_description = "Toggle the display of the function and properties"

    data_path: StringProperty()
    value: StringProperty()

    def execute(self, context):
        data_path = self.data_path.split(".")
        attr = data_path.pop()
        data = context

        for path in data_path:
            data = getattr(data, path)
        prop_collection = getattr(data, attr)

        for index, item in enumerate(prop_collection):
            if item.value == self.value:
                prop_collection.remove(index)
                break
        else:
            new_item = prop_collection.add()
            new_item.value = self.value

        return {'FINISHED'}


# -------------------------------------------------------------
#                        Property Group
# -------------------------------------------------------------


class CODE_MAP_PG_properties(PropertyGroup):
    value: StringProperty()

    display_classes: BoolProperty(default=True, description="Show Classes")
    display_variables: BoolProperty(default=True, description="Show Variables")
    display_functions: BoolProperty(default=True, description="Show Functions")
    display_class_functions: BoolProperty(default=True, description="Show Class Functions")
    display_properties: BoolProperty(default=True, description="Show Properties")


# -------------------------------------------------------------
#                          Draw Helper
# -------------------------------------------------------------


class DrawHelper:
    def draw(self, layout, context, text, wm):
        load_icons()

        props = wm.code_map_properties
        prefs = bpy.context.preferences.addons[__package__].preferences

        row = layout.row()
        if prefs.auto_activate_search:
            row.activate_init = True
        row.prop(wm, "search", text="", icon="VIEWZOOM")

        # Check if the toggle is enabled in the addon preferences
        if prefs.display_code_filters:
            layout.separator(factor=0.1)

            row = layout.row(align=True)
            row.scale_x = 5.0

            row.prop(props, "display_classes", text="", icon_value=custom_icons["class"].icon_id, toggle=True)
            row.prop(props, "display_class_functions", text="", icon_value=custom_icons["method"].icon_id, toggle=True)
            row.prop(props, "display_properties", text="", icon_value=custom_icons["property"].icon_id, toggle=True)
            row.prop(props, "display_functions", text="", icon_value=custom_icons["function"].icon_id, toggle=True)
            row.prop(props, "display_variables", text="", icon_value=custom_icons["variable"].icon_id, toggle=True)

            layout.separator(factor=0.1)

        if props.display_classes and prefs.display_class_type:
            layout.prop(prefs, "code_filter_type", text="")

        if text is not None:
            class_name = None
            is_class_name = False

            # Check if there is a class in the current text block
            has_class = any(line.body.startswith("class ") for line in text.lines)

            for i, line in enumerate(text.lines):
                # Check if the search term is in the line
                search_in_line = wm.search.lower() in line.body.lower()

                # Check for class and function lines
                if line.body.startswith("class "):
                    class_name, base_class = self.parse_class_line(line.body)
                    has_methods = self.has_methods(text.lines[i + 1:], class_name)
                    is_class_name = any(item.value == class_name for item in wm.display_def_lines)

                    if self.is_match(wm.search, class_name, line, has_methods) and props.display_classes:
                        self.draw_class_row(layout, context, text, class_name, base_class,
                                            has_methods, is_class_name, i, wm)

                # Check for constants
                elif " = " in line.body and not line.body.startswith(" ") and not line.body.startswith("#") and search_in_line and props.display_variables:
                    self.draw_variable_row(layout, text, line.body, i, has_class, wm)

                # Check for functions
                elif line.body.startswith("def ") and search_in_line and props.display_functions:
                    self.draw_function_row(layout, context, text, line.body, i, has_class, wm)

                # Check for functions inside a class
                elif line.body.startswith("    def ") and is_class_name and search_in_line and props.display_class_functions:
                    self.draw_class_function_row(layout, text, line.body, i)

                # Check for properties
                elif ": " in line.body and is_class_name and not line.body[4].isspace() and not line.body.startswith("#") and search_in_line and props.display_class_functions:
                    self.draw_property_row(layout, text, line.body, i)

                # Check for properties and functions inside a class for wm.search
                elif wm.search.strip():
                    if ": " in line.body and not line.body[4].isspace() and search_in_line:
                        self.draw_property_row(layout, text, line.body, i)

                    elif line.body.startswith("    def ") and search_in_line:
                        self.draw_class_function_row(layout, text, line.body, i)
        else:
            layout.active = False

    def parse_class_line(self, line):
        class_name = line.split("(")[0].replace("class ", "").strip().replace(":", "").strip()

        # Check if there is a base class specified
        if "(" in line and ")" in line:
            base_class = line.split("(")[1].split(")")[0].replace("bpy.types.", "").strip()
        else:
            base_class = None

        return class_name, base_class

    def has_methods(self, lines, class_name):
        for l in lines:
            if l.body.startswith("class "):
                break
            if l.body.startswith("    def ") or (
                    ": " in l.body and not l.body[4].isspace()):
                return True
        return False

    def is_match(self, search, class_name, line, has_methods):
        return search.lower() in class_name.lower() or (
            has_methods and search.lower() in line.body.lower())

    def truncate_text(self, text, max_length=37):
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text

    def get_indentation(self, version):
        if version >= (3, 0, 0):
            return "            "
        else:
            return "    "

    def get_class_type(self, class_name, base_class):
        if "Panel" in base_class:
            return "PANEL"
        elif "Operator" in base_class:
            return "OPERATOR"
        elif "PropertyGroup" in base_class:
            return "PROPERTY_GROUP"
        elif "UIList" in base_class:
            return "UI_LIST"
        elif "AddonPreferences" in base_class:
            return "ADDON_PREFERENCES"
        else:
            return "UNKNOWN"

    def draw_variable_row(self, layout, text, line, i, has_class, wm):
        row = layout.row(align=True)
        row.alignment = 'LEFT'

        if has_class and not wm.search.strip():
            row.label(text="", icon="BLANK1")

        # Get the first word from the line
        constant = line.split()[0]
        constant = self.truncate_text(constant)

        row.operator("code_map.jump", text=constant, icon_value=custom_icons["variable"].icon_id,
                     emboss=False).line_number = i + 1

    def draw_function_row(self, layout, context, text, line, i, has_class, wm):
        prefs = context.preferences.addons[__package__].preferences
        
        row = layout.row(align=True)
        sub = row.row(align=True)  # Align the sub-row containing the operator and label
        sub.alignment = 'LEFT'

        if has_class:
            sub.label(text="", icon="BLANK1")

        # Get the first word from the line
        function = line.split(' ', 1)[1].split('(')[0]
        function = self.truncate_text(function)

        sub = row.row()
        sub.alignment = 'LEFT'
        sub.operator("code_map.jump", text=function, icon_value=custom_icons["function"].icon_id,
                     emboss=False).line_number = i + 1
        
        if prefs.display_function_indicator:
            if len(text.lines) > 900:
                return
            # Optimize AST parsing and indicator display:
            if not hasattr(self, "_ast_cache"):
                self._ast_cache = {}  # Cache for parsed AST trees

            tree = self._ast_cache.get(text.as_string())
            if tree is None:
                try:
                    tree = ast.parse(text.as_string())
                    self._ast_cache[text.as_string()] = tree  # Store parsed tree in cache
                except (SyntaxError, IndentationError, ValueError, TypeError,
                        OverflowError, ModuleNotFoundError, AttributeError, MemoryError, RecursionError):
                    pass

            func_node = {}  # Initialize func_node as an empty dictionary
            if tree is not None:
                func_node = {node.name: (node.lineno, node.end_lineno) for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
                        
            # Check if the current line index is within the lines of the class
            current_line_index = text.current_line_index
            if function in func_node and func_node[function][0] <= current_line_index + 1 <= func_node[function][1]:
                sub = row.row()
                sub.alignment = 'RIGHT'
                sub.label(text="", icon="LAYER_ACTIVE")

    def draw_class_row(self, layout, context, text, class_name, base_class, has_methods, is_class_name, i, wm):
        prefs = context.preferences.addons[__package__].preferences

        try:
            code_element_type = self.get_class_type(class_name, base_class)
        except Exception as e:
            code_element_type = "UNKNOWN"

        if prefs.code_filter_type == "ALL" or prefs.code_filter_type == code_element_type:
            row = layout.row(align=True)
            sub = row.row(align=True)  # Align the sub-row containing the operator and label
            sub.alignment = 'LEFT'

            icon = 'BLANK1' if not has_methods else 'DOWNARROW_HLT' if is_class_name else 'RIGHTARROW'

            # Dynamically show an arrow icon for classes with functions,
            # or a blank icon if the class has no functions
            prop = sub.operator("code_map.toggle_string", text="", icon=icon, emboss=False)
            prop.data_path = "window_manager.display_def_lines"
            prop.value = class_name

            if wm.search.strip():
                sub.enabled = False

            sub = row.row()
            sub.alignment = 'LEFT'
            sub.operator("code_map.jump", text=class_name, icon_value=custom_icons["class"].icon_id,
                         emboss=False).line_number = i + 1

            if prefs.display_class_indicator:
                if len(text.lines) > 900:
                    return
                # Optimize AST parsing and indicator display:
                if not hasattr(self, "_ast_cache"):
                    self._ast_cache = {}  # Cache for parsed AST trees

                tree = self._ast_cache.get(text.as_string())
                if tree is None:
                    try:
                        tree = ast.parse(text.as_string())
                        self._ast_cache[text.as_string()] = tree  # Store parsed tree in cache
                    except (SyntaxError, IndentationError, ValueError, TypeError,
                            OverflowError, ModuleNotFoundError, AttributeError, MemoryError, RecursionError):
                        pass

                class_node = None
                if tree is not None:
                    # Find the node corresponding to the current class
                    class_node = next((node for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and node.name == class_name), None)
                    
                # Check if the current line index is within the lines of the class
                current_line_index = context.space_data.text.current_line_index
                if class_node and class_node.lineno <= current_line_index + 1 <= class_node.end_lineno:
                    sub = row.row()
                    sub.alignment = 'RIGHT'
                    sub.label(text="", icon="LAYER_ACTIVE")

    def draw_property_row(self, layout, text, line, i):
        properties = [
            "BoolProperty", "BoolVectorProperty", "CollectionProperty",
            "EnumProperty", "FloatProperty", "FloatVectorProperty",
            "IntProperty", "IntVectorProperty", "PointerProperty",
            "RemoveProperty", "StringProperty"
        ]

        if any(keyword in line for keyword in properties):
            row = layout.row(align=True)
            row.alignment = 'LEFT'
            row.label(text=self.get_indentation(bpy.app.version))

            # Get the first word from the line
            variable = line.split()[0].split(':')[0]
            variable = self.truncate_text(variable)

            row.operator("code_map.jump", text=variable, icon_value=custom_icons["property"].icon_id,
                         emboss=False).line_number = i + 1


    def draw_class_function_row(self, layout, text, line, i):
        row = layout.row(align=True)
        row.alignment = 'LEFT'
        row.label(text=self.get_indentation(bpy.app.version))

        # Get the second word from the line
        method = line.split(' ', 1)[1].split('(')[0].replace("def ", "").strip()
        method = self.truncate_text(method)

        row.operator("code_map.jump", text=method, icon_value=custom_icons["method"].icon_id,
                     emboss=False).line_number = i + 1


# -------------------------------------------------------------
#                         Popup, Panel
# -------------------------------------------------------------


class CODE_MAP_OT_popup(Operator):
    bl_idname = "code_map.popup"
    bl_label = "Code Map"

    @classmethod
    def poll(cls, context):
        prefs = bpy.context.preferences.addons[__package__].preferences
        return prefs.enable_code_map

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Code Map", icon="WORDWRAP_ON")

        text = bpy.context.space_data.text
        wm = context.window_manager

        draw_helper = DrawHelper()
        draw_helper.draw(layout, context, text, wm)


class CODE_MAP_PT_panel(Panel):
    bl_idname = "CODE_MAP_PT_panel"
    bl_label = "Code Map"
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Code Map"

    @classmethod
    def poll(cls, context):
        prefs = bpy.context.preferences.addons[__package__].preferences
        return prefs.enable_code_map

    def draw(self, context):
        layout = self.layout

        text = bpy.context.space_data.text
        wm = context.window_manager

        draw_helper = DrawHelper()
        draw_helper.draw(layout, context, text, wm)


# ------------------------------


classes = [
    CODE_MAP_OT_jump,
    CODE_MAP_OT_dynamic_toggle,
    CODE_MAP_OT_popup,
]


addon_keymaps = []


def register():
    try:
        bpy.utils.register_class(CODE_MAP_PG_properties)
        WindowManager.display_def_lines = CollectionProperty(type=CODE_MAP_PG_properties)
        WindowManager.code_map_properties = PointerProperty(type=CODE_MAP_PG_properties)

        WindowManager.search = StringProperty(
            name="Search", description="Search for class, funcion, variable amd method")
    except:
        pass

    for cls in classes:
        bpy.utils.register_class(cls)

    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Text', space_type='TEXT_EDITOR')

        kmi = km.keymap_items.new(CODE_MAP_OT_popup.bl_idname, 'ACCENT_GRAVE', 'PRESS')
        addon_keymaps.append((km, kmi))


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    bpy.utils.unregister_class(CODE_MAP_PG_properties)
    del WindowManager.code_map_properties
    del WindowManager.display_def_lines
    del WindowManager.search

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    unload_icons()

    bpy.utils.unregister_class(CODE_MAP_PT_panel)
