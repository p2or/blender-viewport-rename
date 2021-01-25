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
# <pep8 compliant>

import bpy
import re

bl_info = {
    "name": "Viewport Rename",
    "author": "Christian Brinkmann (p2or)",
    "description": "Rename, find and select Objects directly in the Viewport",
    "version": (0, 7),
    "blender" : (2, 81, 0),
    "location": "3D View > Ctrl+R",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "https://github.com/p2or/blender-viewport-rename",
    "tracker_url": "https://github.com/p2or/blender-viewport-rename/issues",
    "category": "3D View"
}

# ------------------------------------------------------------------------
#    Operator(s)
# ------------------------------------------------------------------------

class VIEW3D_OT_viewport_rename(bpy.types.Operator):
    """Rename, find and select Objects directly in the Viewport"""
    bl_idname = "view3d.viewport_rename"
    bl_label = "Viewport Rename"
    bl_options = {'REGISTER', 'UNDO'}
    bl_property = "new_name"

    new_name : bpy.props.StringProperty(name="New Name")
    substitute : bpy.props.StringProperty(name="Replace")
    data_flag : bpy.props.BoolProperty(name="Rename Data-Block", default=False)
    mode : bpy.props.EnumProperty(name="Mode", description="Set the Mode",
        items = [('RENAME', "Rename", ""),
                ('RESEARCH', "Search & Replace", ""),
                ('SEARCH', "Search & Select", "")])

    @classmethod
    def poll(cls, context):
        return bool(context.active_object) #selected_objects

    def execute(self, context):
        user_input = self.new_name
        
        if not user_input:
            self.report({'INFO'}, "No input, operation cancelled")
            return {'CANCELLED'}
        
        # -------------------------------------------------------
        
        if self.mode == 'RENAME':
            reverse = False
            if user_input.endswith("#r"):
                reverse = True
                user_input = user_input[:-1]

            suff = re.findall("#+$", user_input)
            if user_input and suff:
                number = ('%0'+str(len(suff[0]))+'d', len(suff[0]))
                real_name = re.sub("#", '', user_input)           

                objs = context.selected_objects[::-1] if reverse else context.selected_objects
                names_before = [n.name for n in objs]
                for c, o in enumerate(objs, start=1):
                    o.name = (real_name + (number[0] % c))
                    if self.data_flag and o.data is not None:
                        o.data.name = (real_name + (number[0] % c))
                self.report({'INFO'}, "Renamed {}".format(", ".join(names_before)))
                return {'FINISHED'}

            elif user_input:
                old_name = context.active_object.name
                context.active_object.name = user_input
                if self.data_flag and context.active_object.data is not None:
                    context.active_object.data.name = user_input
                self.report({'INFO'}, "{} renamed to {}".format(old_name, user_input))
                return {'FINISHED'}
        
        # -------------------------------------------------------
        
        elif self.mode == 'SEARCH':
            candidates = []
            if self.data_flag:
                for obj in context.scene.objects:
                    if obj.data is not None and self.new_name in obj.data.name:
                        candidates.append(obj)
            else:
                for obj in context.scene.objects:
                    if self.new_name in obj.name:
                        candidates.append(obj)

            if candidates:
                bpy.ops.object.select_all(action='DESELECT')
                for obj in candidates:
                    # limited by current API state,
                    # should be replaced with visible_set(True) when available
                    if obj.visible_get():
                        obj.select_set(True)
                cand_names = [n.name for n in candidates]
                self.report({'INFO'}, "Found {} object(s): {}".format(len(cand_names), ", ".join(cand_names)))
                return {'FINISHED'}

            else:

                bpy.ops.object.select_all(action='DESELECT')
                self.report({'INFO'}, "Nothing found.")
                return {'CANCELLED'}

        # -------------------------------------------------------
        
        elif self.mode == 'RESEARCH':
            candidates = []
            for obj in context.selected_objects:
                if self.new_name in obj.name:
                    candidates.append(obj)

            if candidates:
                for obj in candidates:
                    obj.name = obj.name.replace(self.new_name, self.substitute)
                    if self.data_flag and obj.data is not None:
                        obj.data.name = obj.name
                self.report({'INFO'}, "Renamed {} objects".format(len(candidates)))
                return {'FINISHED'}
            else:
                if context.selected_objects:
                    self.report({'INFO'}, 'No object names in scene containing "{}"'.format(self.new_name))
                else:
                    self.report({'INFO'}, "Nothing selected in the viewport.")
                return {'CANCELLED'}


    def invoke(self, context, event):
        if context.active_object:
            self.new_name = context.active_object.name
        return context.window_manager.invoke_props_dialog(self, width=450)

    def draw(self, context):
        txt_name = "New Name" if self.mode == "RENAME" else "Search for"
        txt_data = "Rename Data-Block" if self.mode != "SEARCH" else "Find Data-Block"

        layout = self.layout
        layout.row()
        layout.prop(self, "mode", expand=True)
        layout.row()
        layout.prop(self, "new_name", text=txt_name)

        if self.mode == "RESEARCH":
            rep = layout.row()
            rep.prop(self, "substitute", text="Replace with")

        layout.prop(self, "data_flag", text=txt_data)
        layout.row()


def draw_viewport_rename_obj_menu(self, context):
    layout = self.layout 
    layout.separator()
    layout.operator(VIEW3D_OT_viewport_rename.bl_idname, text="Seek and Rename",  icon='FONTPREVIEW')


# ------------------------------------------------------------------------
#    Register, unregister and hotkeys
# ------------------------------------------------------------------------

addon_keymaps = []

def register():
    addon_keymaps.clear()
    bpy.utils.register_class(VIEW3D_OT_viewport_rename)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new(VIEW3D_OT_viewport_rename.bl_idname, type='R', value='PRESS', ctrl=True)
        addon_keymaps.append((km, kmi))

    bpy.types.VIEW3D_MT_object.append(draw_viewport_rename_obj_menu)


def unregister():
    bpy.types.VIEW3D_MT_object.remove(draw_viewport_rename_obj_menu)

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    bpy.utils.unregister_class(VIEW3D_OT_viewport_rename)

if __name__ == "__main__":
    register()
