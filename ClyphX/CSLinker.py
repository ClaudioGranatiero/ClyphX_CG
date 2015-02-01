"""
# Copyright (C) 2014-2015 Stray <stray411@hotmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# For questions regarding this module contact
# Stray <stray411@hotmail.com>
"""

from _Framework.ControlSurfaceComponent import ControlSurfaceComponent
from _Framework.ControlSurface import ControlSurface
from _Framework.SessionComponent import SessionComponent

class CSLinker(ControlSurfaceComponent):
    """ CSLinker links the SessionComponents of two control surface scripts in Live 9. """
    
    def __init__(self):
        ControlSurfaceComponent.__init__(self)
        self._slave_objects = [None, None]
        self._script_names = None
        self._horizontal_link = False
        self._matched_link = False
        
        
    def disconnect(self):
        """ Extends standard to disconnect and remove slave objects. """
        for obj in self._slave_objects:
            if obj:
                obj.disconnect()
        self._slave_objects = None
        ControlSurfaceComponent.disconnect(self)
        
        
    def parse_settings(self, settings_string):
        """ Parses settings data read from UserPrefs for linker settings. """
        line_data = settings_string.split('=')
        if 'MATCHED' in line_data[0]:
            self._matched_link = line_data[1].strip() == 'TRUE'
        elif 'HORIZ' in line_data[0] and not self._matched_link:
            self._horizontal_link = line_data[1].strip() == 'TRUE'
        else:
            if 'NONE' in line_data[1]:
                self._script_names = None
            else:
                if '1' in line_data[0]:
                    self._script_names = [line_data[1].strip()]
                else:
                    if self._script_names:
                        self._script_names.append(line_data[1].strip())
                        self.connect_script_instances(self.canonical_parent._control_surfaces())
                            
        
    def connect_script_instances(self, instanciated_scripts):
        """ Attempts to find the two specified scripts, find their SessionComponents and create slave objects for them. """ 
        if self._script_names:
            scripts = [None, None]
            found_scripts = False
            scripts_have_same_name = self._script_names[0] == self._script_names[1]
            for script in instanciated_scripts:
                if isinstance(script, ControlSurface) and script.components:
                    script_name = script.__class__.__name__.upper() 
                    if script_name == self._script_names[0]:
                        if scripts_have_same_name:
                            scripts[scripts[0] != None] = script
                        else:
                            scripts[0] = script
                    elif script_name == self._script_names[1]:
                        scripts[1] = script
                    found_scripts = scripts[0] and scripts[1]
                    if found_scripts:
                        break
            if found_scripts:
                self.canonical_parent.log_message('CSLINKER SUCCESS: Specified scripts located!')
                ssn_comps = []
                for script in scripts:
                    for c in script.components:
                        if isinstance (c, SessionComponent):
                            ssn_comps.append(c)
                            break
                if len(ssn_comps) == 2:
                    self.canonical_parent.log_message('CSLINKER SUCCESS: SessionComponents for specified scripts located!')
                    if self._matched_link:
                        for s in ssn_comps:
                            s._link()
                    else:
                        self._slave_objects[0] = SessionSlave(self._horizontal_link, ssn_comps[0], ssn_comps[1], -(ssn_comps[0].width()) if self._horizontal_link else -(ssn_comps[0].height()))
                        self._slave_objects[1] = SessionSlaveSecondary(self._horizontal_link, ssn_comps[1], ssn_comps[0], ssn_comps[0].width() if self._horizontal_link else ssn_comps[0].height())
                        self._refresh_slave_objects()
                else:
                    self.canonical_parent.log_message('CSLINKER ERROR: Unable to locate SessionComponents for specified scripts!')       
            else:
                self.canonical_parent.log_message('CSLINKER ERROR: Unable to locate specified scripts!')                 
                
                
    def on_track_list_changed(self):
        """ Refreshes slave objects if horizontally linked. """
        if self._horizontal_link and not self._matched_link:
            self._refresh_slave_objects()            
        
        
    def on_scene_list_changed(self):
        """ Refreshes slave objects if vertically linked. """
        if not self._horizontal_link and not self._matched_link:
            self._refresh_slave_objects() 
            
        
    def _refresh_slave_objects(self):
        """ Refreshes offsets of slave objects. """
        for obj in self._slave_objects:
            if obj:
                obj._on_offsets_changed()
                    
                    
class SessionSlave(object):
    """ SessionSlave is the base class for linking two SessionComponents. """
    
    def __init__(self, horz_link, self_comp, observed_comp, offset):
        self._horizontal_link = horz_link
        self._offset = offset
        self._self_ssn_comp = self_comp
        self._observed_ssn_comp = observed_comp
        self._last_self_track_offset = -1
        self._last_self_scene_offset = -1
        self._last_observed_track_offset = -1
        self._last_observed_scene_offset = -1
        self._num_tracks = -1
        self._num_scenes = -1
        self._observed_ssn_comp.add_offset_listener(self._on_offsets_changed)
        
        
    def disconnect(self):
        self._self_ssn_comp = None
        self._observed_ssn_comp.remove_offset_listener(self._on_offsets_changed)
        self._observed_ssn_comp = None
    
    
    def _on_offsets_changed(self):
        """ Called on offset changes to the observed SessionComponent to handle moving offsets if possible. """
        if self._horizontal_link:
            new_num_tracks = len(self._self_ssn_comp.tracks_to_use())
            if new_num_tracks != self._num_tracks: # if track list changed, need to completely refresh offsets
                self._num_tracks = new_num_tracks
                self._last_self_track_offset = -1
                self._last_observed_track_offset = -1
            observed_offset = self._observed_ssn_comp.track_offset()
            if observed_offset != self._last_observed_track_offset: # if observed offset unchanged, do nothing
                self._last_observed_track_offset = observed_offset
                if self._track_offset_change_possible():
                    self_offset = max(self._min_track_offset(), min(self._num_tracks, (self._last_observed_track_offset + self._offset)))
                    if self_offset != self._last_self_track_offset: # if self offset unchanged, do nothing
                        self._last_self_track_offset = self_offset
                        self._self_ssn_comp.set_offsets(self._last_self_track_offset, self._self_ssn_comp.scene_offset())
                else:
                    return
        else:
            new_num_scenes = len(self._self_ssn_comp.song().scenes)
            if new_num_scenes != self._num_scenes: # if scene list changed, need to completely refresh offsets
                self._num_scenes = new_num_scenes
                self._last_self_scene_offset = -1
                self._last_observed_scene_offset = -1
            observed_offset = self._observed_ssn_comp.scene_offset()
            if observed_offset != self._last_observed_scene_offset: # if observed offset unchanged, do nothing
                self._last_observed_scene_offset = observed_offset
                if self._scene_offset_change_possible():
                    self_offset = max(self._min_scene_offset(), min(self._num_scenes, (self._last_observed_scene_offset + self._offset)))
                    if self_offset != self._last_self_scene_offset: # if self offset unchanged, do nothing
                        self._last_self_scene_offset = self_offset
                        self._self_ssn_comp.set_offsets(self._self_ssn_comp.track_offset(), self._last_self_scene_offset)
                else:
                    return
                
                
    def _track_offset_change_possible(self):
        """ Returns whether or not moving the track offset is possible. """
        return self._num_tracks > self._self_ssn_comp.width()
    
    
    def _min_track_offset(self):
        """ Returns the minimum track offset. """
        return 0
    
    
    def _scene_offset_change_possible(self):
        """ Returns whether or not moving the scene offset is possible. """
        return self._num_scenes > self._self_ssn_comp.height()
    
    
    def _min_scene_offset(self):
        """ Returns the minimum scene offset. """
        return 0
    

class SessionSlaveSecondary(SessionSlave):
    """ SessionSlaveSecondary is the second of the two linked slave objects. 
    This overrides the functions that return whether offsets can be changed as well as the functions that return minimum offsets. """
    
    
    def _track_offset_change_possible(self):
        return self._num_tracks >= self._self_ssn_comp.width() + self._observed_ssn_comp.width()
    
    
    def _min_track_offset(self):
        return self._last_observed_track_offset
    
    
    def _scene_offset_change_possible(self):
        return self._num_scenes >= self._self_ssn_comp.height() + self._observed_ssn_comp.height()
    
    
    def _min_scene_offset(self):
        return self._last_observed_scene_offset
    