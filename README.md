### Viewport Rename

A simple Blender Add-on to rename the selected object as well as batch rename selected objects in *3d View*.

<img width="481" alt="Screenshot 2021-06-19 at 22 25 26" src="https://user-images.githubusercontent.com/512368/122654671-509bb200-d14d-11eb-9c9e-f5e0e930ccfa.png">

#### Usage

Once the Add-on is enabled, you can press <kbd>Ctrl</kbd><kbd>R</kbd> to enter a 'new name' for the *active object* as well as rename its data block (optional). In order to speed up the process you can hit <kbd>Return</kbd> followed by <kbd>O</kbd> to confirm, after typing the 'new name':

![intro](https://i.sstatic.net/dAdHN.gif)

The Add-on also allows to *batch rename* all objects in the current selection. The suffix is determined by the given number of hash characters at the end of the string. You can simply type `Cube-###` to get *'Cube-001'*, *'Cube-002'* and *'Cube-003'* as well as `Cube-###r` to get a reversed list.

![intro](https://i.sstatic.net/2mDxx.gif)

#### Installation

 1. Download the [latest release](https://github.com/p2or/blender-viewport-rename/releases/)
 2. In Blender open up *User Preferences > Addons*
 3. Click *Install from File*, select `blender-viewport-rename.py` and activate the Add-on
 
 ----
*The add-on has emerged from: [Is there an addon for renaming an object with a keyboard shortcut?](https://blender.stackexchange.com/q/60649)*
