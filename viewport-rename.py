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
import fnmatch

bl_info = {
    "name": "Viewport Rename",
    "author": "Christian Brinkmann (p2or)",
    "description": "Rename, find and select Objects directly in the Viewport",
    "version": (0, 9, 0),
    "blender": (3, 6, 0),
    "location": "3D View > Ctrl+R, Ctrl+F",
    "warning": "",  # used for warning icon and text in addons panel
    "doc_url": "https://github.com/p2or/blender-viewport-rename",
    "tracker_url": "https://github.com/p2or/blender-viewport-rename/issues",
    "category": "3D View"
}


# -------------------------------------------------------------------
#    Operator(s)
# -------------------------------------------------------------------


class VIEW3D_OT_viewport_rename(bpy.types.Operator):
    """Rename, find and select Objects directly in the Viewport"""
    bl_idname = "view3d.viewport_rename"
    bl_label = "Viewport Rename"
    bl_options = {'REGISTER', 'UNDO'}
    bl_property = "new_name"

    new_name: bpy.props.StringProperty(name="New Name")
    start: bpy.props.IntProperty(name="Start", default=1)
    substitute: bpy.props.StringProperty(name="Replace")
    data_flag: bpy.props.BoolProperty(name="Rename Data-Block", default=False)
    reverse_flag: bpy.props.BoolProperty(name="Reverse List", default=False)
    scope: bpy.props.EnumProperty(
        name="Scope",
        description="Select the scope of the operation",
        items=[
            ('SELECTED', "Selected Objects",
             "Operate only on selected objects"),
            ('SCENE', "All Objects in Scene",
             "Operate on all objects in the scene"),
        ],
        default='SCENE'
    )
    mode: bpy.props.EnumProperty(
        name="Mode",
        description="Select the operation mode",
        items=[
            ('RENAME', "Rename",
             "Batch rename selected objects"),
            ('SEARCH', "Find & Select",
             "Find and select objects in the scene by given name "
             "(supports wildcards e.g. #, *, ? for searching)"),
            ('RESEARCH', "Find & Replace",
             "Replace text within object names in the scene "
             "(supports wildcards e.g. #, *, ? for searching)"),
        ],
        default='RENAME'
    )

    
    def set_property(self, target_object, property_name, value):
        """
        Safely assign a value to an object or data-block,
        avoiding Depsgraph updates if unchanged, and catching
        errors if the property is read-only (e.g. linked data).
        """
        prop = getattr(target_object, property_name, None)
        if prop is not None:
            try:
                if prop != value: 
                    setattr(target_object, property_name, value)
                    return True
            except (AttributeError, RuntimeError):
                # Fails safely on Linked Data or pure read-only properties
                pass
        return False

    @classmethod
    def poll(cls, context):
        return bool(context.active_object)

    def execute(self, context):
        user_input = self.new_name.strip()

        selected_objects = sorted(
            context.selected_objects, 
            key=lambda o: o.name, 
            reverse=self.reverse_flag
        )

        # -------------------------------------------------------

        if self.mode == 'RENAME':
            
            if not user_input and not self.data_flag:
                self.report({'INFO'}, "No input, rename operation cancelled.")
                return {'CANCELLED'}

            if "#r" in user_input:
                self.reverse_flag = True
                user_input = user_input.replace("#r", "#")
            
            hashes = user_input.count("#")
            hash_str = "#" * hashes
            target_objects = (
                [context.active_object] if hashes == 0 else selected_objects
            )
            renamed = []

            for c, o in enumerate(target_objects, start=self.start):
                user_name = user_input
                if hashes > 0:
                    user_name = user_input.replace(hash_str, str(c).zfill(hashes))

                changed = False
                original_name = o.name
                
                if user_name:
                    if self.set_property(o, "name", user_name):
                        changed = True
                
                if self.data_flag:  # Copy the new name to the datablock
                    if self.set_property(o.data, "name", o.name):
                        changed = True
                
                if changed:
                    renamed.append(original_name)

            if renamed:
                msg = "Renamed {}".format(", ".join(renamed))
            else:
                msg = "Skipped (possibly due to no name changes, or linked data)."
            
            self.report({'INFO'}, msg)
            return {'FINISHED'}

        # -------------------------------------------------------

        # Convert '#' to '?' to allow hash-based wildcard searching
        if "#" in user_input and not any(c in user_input for c in "*?["):
            user_input = f"*{user_input}"
        user_input = user_input.replace("#", "?")

        pattern = (
            user_input if any(c in user_input for c in "*?[")
            else f"*{user_input}*"
        )
        pool = context.scene.objects if self.scope == 'SCENE' else selected_objects

        candidates = [
            obj for obj in pool
            if fnmatch.fnmatchcase(obj.name, pattern) or (
                self.data_flag
                and getattr(obj, "data", None)
                and fnmatch.fnmatchcase(obj.data.name, pattern)
            )
        ]

        # -------------------------------------------------------

        if self.mode == 'SEARCH':

            if not candidates:
                self.report({'INFO'}, "Nothing found.")
                return {'CANCELLED'}

            selected_names = []
            bpy.ops.object.select_all(action='DESELECT')
            for obj in candidates:
                # Check visibility and selectability before selecting
                if obj.visible_get() and not obj.hide_select:
                    try:
                        obj.select_set(True)
                        selected_names.append(obj.name)
                    except RuntimeError:
                        pass

            cand_names = [o.name for o in candidates]
    
            if selected_names:
                msg = "Selected {} of {} found objects: {}".format(
                    len(selected_names), len(cand_names), ", ".join(selected_names)
                )
            else:
                msg = "Nothing selected (possibly due to visibility or selectability)."
            
            self.report({'INFO'}, msg)
            return {'FINISHED'}

        # -------------------------------------------------------
        
        elif self.mode == 'RESEARCH':

            if not candidates:
                scope_str = "scene" if self.scope == 'SCENE' else "selection"
                self.report(
                    {'INFO'}, 
                    f'No object names in {scope_str} matching "{user_input}"'
                )
                return {'CANCELLED'}

            replace_target = user_input.replace("*", "").replace("?", "")
            renamed_objects = []
            
            if not replace_target:
                self.report({'INFO'}, "Nothing to replace.")
                return {'CANCELLED'}
            
            for obj in candidates:
                if replace_target in obj.name:
                    new_name = obj.name.replace(replace_target, self.substitute)
                    
                    changed = False
                    if self.set_property(obj, "name", new_name):
                        changed = True
                        
                    if self.data_flag:
                        if self.set_property(obj.data, "name", new_name):
                            changed = True
                            
                    if changed:
                        renamed_objects.append(obj.name)
            
            if renamed_objects:
                msg = "Renamed {} objects: {}".format(
                    len(renamed_objects), ", ".join(renamed_objects)
                )
            else:
                msg = "All objects skipped (possibly due to linked data or no matches)."
            
            self.report({'INFO'}, msg)
            return {'FINISHED'}

    def check(self, context):
        return True

    def invoke(self, context, event):
        self.new_name = name = context.active_object.name
        name_clean = name.rstrip('0123456789')
        if name_clean and name_clean != name:
            self.new_name = name_clean[:-1] if name_clean[-1] in ".-_ " else name_clean

        return context.window_manager.invoke_props_dialog(self, width=450)

    def draw(self, context):
        txt_name = "New Name" if self.mode == "RENAME" else "Search for"
        txt_data = (
            "Rename Data-Block" if self.mode != "SEARCH" else "Search for Data-Block"
        )

        layout = self.layout
        layout.row().prop(self, "mode", expand=True)

        if self.mode != "RENAME":
            layout.row().prop(self, "scope")
        if self.mode == "RENAME":
            spl = layout.split(factor=0.8, align=True)
            spl.prop(self, "new_name", text=txt_name)
            col = spl.column(align=True)
            col.prop(self, "start", text="")
            col.active = "#" in self.new_name
        else:
            layout.row().prop(self, "new_name", text=txt_name)

        if self.mode == "RESEARCH":
            rep = layout.row()
            rep.prop(self, "substitute", text="Replace with")

        layout.row()
        layout.prop(self, "data_flag", text=txt_data)
        layout.row()


def draw_viewport_rename_obj_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.operator(VIEW3D_OT_viewport_rename.bl_idname,
                    text="Viewport Rename", icon='FONTPREVIEW')


# -------------------------------------------------------------------
#    Registration & Shortcuts
# -------------------------------------------------------------------

addon_keymaps = []


def register():
    addon_keymaps.clear()
    bpy.utils.register_class(VIEW3D_OT_viewport_rename)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(
            name='3D View', space_type='VIEW_3D'
        )
        
        kmi_r = km.keymap_items.new(
            VIEW3D_OT_viewport_rename.bl_idname,
            type='R',
            value='PRESS',
            ctrl=True
        )
        kmi_r.properties.mode = 'RENAME'
        addon_keymaps.append((km, kmi_r))
        
        kmi_f = km.keymap_items.new(
            VIEW3D_OT_viewport_rename.bl_idname,
            type='F',
            value='PRESS',
            ctrl=True
        )
        kmi_f.properties.mode = 'SEARCH'
        addon_keymaps.append((km, kmi_f))

    bpy.types.VIEW3D_MT_object.append(draw_viewport_rename_obj_menu)


def unregister():
    bpy.types.VIEW3D_MT_object.remove(draw_viewport_rename_obj_menu)

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    bpy.utils.unregister_class(VIEW3D_OT_viewport_rename)


if __name__ == "__main__":
    register()
