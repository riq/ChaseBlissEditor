from kivy.app import App
from kivy.uix.popup import Popup
from kivy.factory import Factory

import cb_pedal_definitions as cb
from os.path import join, exists
from os import mkdir
from copy import deepcopy
import json
from pathlib import Path
from filebrowser import SaveDialog, LoadDialog


class CreateInitFile(Popup):
    pass


class PresetFile:
    # Contents of patch file is driven by contents of the Pedal data class in cb_pedal_definitions.py
    def __init__(self):
        self.preset = {}
        self.opened_preset = {}
        self.patch_file = 'UNTITLED'
        self.filter = ['*.cbp']
        self._set_patch_active = False
        self.app = App.get_running_app()
        self.pedal = cb.pedals[self.app.root.ids.devices.text]
        self.path = join(self.app.user_data_dir, 'Chase Bliss Patches')

    def initialize_patch(self, recall=True):
        self.pedal = cb.pedals[self.app.root.ids.devices.text]
        init_file = Path(self.path) / Path('init_patch_' + self.pedal.name + '.cbp')
        if recall and init_file.exists():
            self._open_selection([init_file])  # Recall the initialization file
            self.app.root.ids.patch_filename.text = 'UNTITLED'
        else:
            pup = CreateInitFile()
            pup.ids.message.text = 'Current settings saved to:  "' + Path(init_file).name + \
                                   '"\nPress "Recall" to recall this setting\n' + \
                                   'This setting will be recalled when this device is selected'
            pup.open()
            self._save_selection([init_file])
            self.app.root.ids.patch_filename.text = 'UNTITLED'

    def recall_initial_patch(self):
        self._set_patch_active = True
        self.pedal = cb.pedals[self.app.root.ids.devices.text]
        init_file = Path(self.path) / Path('init_patch_' + self.pedal.name + '.cbp')
        if init_file.exists():
            self._open_selection([init_file])
        else:
            self._clear_patch()
        self._set_patch_active = False

    def _clear_patch(self):
        self._set_patch_active = True
        p = self.app.root.ids
        p.cc14.knob_value = 0
        p.cc15.knob_value = 0
        p.cc16.knob_value = 0
        p.cc17.knob_value = 0
        p.cc18.knob_value = 0
        p.cc19.knob_value = 0
        p.cc20.knob_value = 0

        p.cc21.text = self.pedal.cc21[0]
        p.cc22.text = self.pedal.cc22[0]
        p.cc23.text = self.pedal.cc23[0]

        p.sm.get_screen('tap_bpm').ids.bpm_input.text = ''
        p.sm.get_screen('tap_bpm').ids.bypass_stomp.state = 'normal'
        p.sm.get_screen('channel_select').ids.left_stomp.state = 'normal'
        p.sm.get_screen('channel_select').ids.right_stomp.state = 'normal'
        p.notes.text = ''
        self._set_patch_active = False

    def _get_patch(self):
        p = self.app.root.ids
        self.pedal = cb.pedals[self.app.root.ids.devices.text]
        self.preset['version'] = 1.0
        self.preset['pedal name'] = self.pedal.name
        self.preset['cc14'] = p.cc14.knob_value
        self.preset['cc15'] = p.cc15.knob_value
        self.preset['cc16'] = p.cc16.knob_value
        self.preset['cc17'] = p.cc17.knob_value
        self.preset['cc18'] = p.cc18.knob_value
        self.preset['cc19'] = p.cc19.knob_value

        # Ramp knob CC
        self.preset['cc20'] = p.cc20.knob_value if self.pedal.cc20 != 'None' else 0

        try:
            self.preset['cc21'] = self.pedal.cc21.index(p.cc21.text) + self.pedal.cc21_offset
            self.preset['cc22'] = 0 if self.pedal.cc22_disabled else self.pedal.cc22.index(p.cc22.text) + 1
            self.preset['cc23'] = 0 if self.pedal.cc23_disabled else self.pedal.cc23.index(p.cc23.text) + 1
        except ValueError as e:
            # print(e)
            pass

        if self.pedal.tap and p.sm.get_screen('tap_bpm').ids.bpm_input.text:
            self.preset['bpm'] = p.sm.get_screen('tap_bpm').ids.bpm_input.text

        if self.pedal.tap:
            self.preset['bypass_stomp'] = p.sm.get_screen('tap_bpm').ids.bypass_stomp.state
        else:  # pedals without tap have 2 channel select stomps
            self.preset['left_stomp'] = p.sm.get_screen('channel_select').ids.left_stomp.state
            self.preset['right_stomp'] = p.sm.get_screen('channel_select').ids.right_stomp.state

        # if p.notes.text:
        self.preset['notes'] = '' if not p.notes.text else p.notes.text

    def _set_device(self, name):
        for key, value in cb.pedals.items():
            if value.name == name:
                # print(f'name match, key: {key}')
                self.app.root.ids.devices.text = key
                self.pedal = cb.pedals[self.app.root.ids.devices.text]
                # print(self.app.root.pedal)
                return

    def _set_patch(self, patch):
        self._set_patch_active = True
        self.preset = deepcopy(patch)  # copy to self.preset...
        self._set_device(self.preset['pedal name'])
        p = self.app.root.ids
        p.cc14.knob_value = self.preset['cc14']
        p.cc15.knob_value = self.preset['cc15']
        p.cc16.knob_value = self.preset['cc16']
        p.cc17.knob_value = self.preset['cc17']
        p.cc18.knob_value = self.preset['cc18']
        p.cc19.knob_value = self.preset['cc19']
        p.cc20.knob_value = self.preset['cc20']   # if 'cc20' in self.preset else 0

        p.cc21.text = self.pedal.cc21[self.preset['cc21'] - self.pedal.cc21_offset]
        p.cc22.text = self.pedal.cc22[0] if self.pedal.cc22_disabled else self.pedal.cc22[self.preset['cc22'] - 1]
        p.cc23.text = self.pedal.cc23[0] if self.pedal.cc23_disabled else self.pedal.cc23[self.preset['cc23'] - 1]

        if 'bpm' in self.preset:
            p.sm.get_screen('tap_bpm').ids.bpm_input.text = self.preset['bpm']
            p.sm.get_screen('tap_bpm').ids.bpm_input.create_tap(None)
        else:
            p.sm.get_screen('tap_bpm').ids.bpm_input.text = ''

        if 'bypass_stomp' in self.preset:
            p.sm.get_screen('tap_bpm').ids.bypass_stomp.state = self.preset['bypass_stomp']
        if 'left_stomp' in self.preset:
            p.sm.get_screen('channel_select').ids.left_stomp.state = self.preset['left_stomp']
        if 'right_stomp' in self.preset:
            p.sm.get_screen('channel_select').ids.right_stomp.state = self.preset['right_stomp']
        p.notes.text = self.preset['notes']
        self._set_patch_active = False

    def open(self):
        if not exists(self.path):
            mkdir(self.path)
        Factory.LoadDialog(path=self.path, filters=self.filter,
                           title='Open Patch File', action=self._open_selection).open()

    def _open_selection(self, selection):
        if not selection:
            return

        with open(selection[0], 'r') as file:
            p = file.read()
            self._set_patch(json.loads(p))
        self.app.root.ids.patch_filename.text = Path(selection[0]).stem
        self.opened_preset = deepcopy(self.preset)
        self.app.root.ids.patch_filename.color = [1, 1, 1, 1]  # set patch color white

    def save(self):
        if not exists(self.path):
            mkdir(self.path)
        file_name = self.app.root.ids.patch_filename.text + '.cbp'
        Factory.SaveDialog(path=self.path, filename=file_name,
                           filters=self.filter, title='Save the Patch',
                           action=self._save_selection).open()

    def _save_selection(self, filename, path):
        if not filename:
            return      # The user did not select a file
        if Path(filename).suffix == '':
            filename = filename + '.cbp'
        filename = Path(path) / filename
        with open(filename, 'w') as file:
            self._get_patch()
            p = json.dumps(self.preset)
            file.write(p)
        self.app.root.ids.patch_filename.text = Path(filename).stem
        self.opened_preset = deepcopy(self.preset)
        self.update_patch_color()

    def update_patch_color(self):
        if self._set_patch_active:
            return
        if self.app.root.ids.patch_filename.text != 'UNTITLED':
            self._get_patch()
            changed = not (self.preset == self.opened_preset)
            self.app.root.ids.patch_filename.color = [1, 0, 0, 1] if changed else [1, 1, 1, 1]
