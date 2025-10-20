import os
import json
import rtmidi
import time

class Player:
    """Gera objetos de comunicação MIDI"""
    def __init__(self):
        self.gyro_midiout = rtmidi.MidiOut().open_port(0)
        self.accel_midiout = self.gyro_midiout

        # Sistema de flag assegura que condicionais só executem em mudanças de estado
        self.touch_flag = False
        self.accel_flag = False

        self.gyro = 0
        self.accel = 0
        self.touch = 0
        self.last_gyro_notes_played = []
        self.last_accel_trigger_time = 0
        self.NOTES = [f"{n}{o}" for o in range(1, 5) for n in ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]]


    def update(self, notes, selected_dial) -> None:
        """Recebe input dos parâmetros do dispositivos e acionar eventos MIDI"""
        
        current_gyro_notes = self.note_to_code(notes[selected_dial])

        # # ACCEL
        # if time.time() - self.last_accel_trigger_time > self.config.get('accel_delay'):
        #     if abs(self.accel) > self.config.get('accel_sensitivity_+') or abs(self.accel) > self.config.get('accel_sensitivity_-'):
        #         if self.config.get('legato'): # Caso legato esteja ativado, a funcionalidade será interromper última nota
        #             self.stop_notes('gyro', self.last_gyro_notes_played)     
        #         self.play_notes('accel', self.get_from_idx(self.config.get('accel_notes')))
        #         self.last_accel_trigger_time = time.time()
        #         self.accel_flag = True
            
        #     elif self.accel_flag:
        #         self.stop_notes('accel', self.get_from_idx(self.config.get('accel_notes')))
        #         self.accel_flag = False    
        
        # TOUCH
        if self.touch: 
            # Início do toque
            if not self.touch_flag:
                # if self.config.get('legato'):
                #     self.stop_notes('gyro', self.last_gyro_notes_played)
                self.play_notes('gyro', current_gyro_notes)
                self.touch_flag = True 
    
            # Decorrer do toque
            if current_gyro_notes != self.last_gyro_notes_played:
                self.stop_notes('gyro', self.last_gyro_notes_played)
                self.play_notes('gyro', current_gyro_notes)
        else:
            # Liberação do toque
            if self.touch_flag:
                # if not self.config.get('legato'): 
                self.stop_notes('gyro', self.last_gyro_notes_played)
                self.touch_flag = False

    # --UTIL FUNCTIONS--
    def note_to_code(self, note) -> list[int]: 
        """Recebe uma lista de notas musicais e retorna uma lista de seus respectivos códigos de nota MIDI"""
        midi_codes = []
        for i in range(len(self.NOTES)):
            if self.NOTES[i] == note:
                midi_codes.append(12 + i)
        return midi_codes #

    def play_notes(self, device, note_codes_list) -> None:
        """Recebe uma lista de códigos de nota MIDI e as aciona"""
        for note_code in note_codes_list: # [36, 40, 43] 
            match device:
                case 'gyro':
                    self.gyro_midiout.send_message([144, 
                                note_code, # 36
                                127])
                    # print(f'[Gyro] On: {note_codes_list}')
                    self.last_gyro_notes_played = note_codes_list
                case 'accel':
                    self.accel_midiout.send_message([144, 
                                    note_code, # 36
                                    100])
                    # print(f'[Accel] On: {note_codes_list}')
    
    def stop_notes(self, device, note_codes_list) -> None:
        """Recebe uma lista de códigos de nota MIDI e as interrompe"""
        for note_code in note_codes_list: # [36, 40, 43]    
            match device:
                case 'gyro':
                    self.gyro_midiout.send_message([128, 
                                        note_code, # 36
                                        100])
                    self.last_gyro_notes_played = note_codes_list
                    # print(f'[Gyro] Off: {note_codes_list}')
                case 'accel':
                    self.accel_midiout.send_message([128, 
                                        note_code, # 36
                                        100])     
                    # print(f'[Accel] Off: {note_codes_list}')   

    # def change_program(self, n) -> None:
    #     """Troca programa"""
    #     self.gyro_midiout.send_message([192 + self.config.get('midi_channel'), 
    #                         n,
    #                         0])

    # def reset_channels(self) -> None:
    #     """Interrompe todos os eventos de um canal"""
    #     self.gyro_midiout.send_message([175 + self.config.get('midi_channel'), 
    #                                 123,
    #                                 0])
    #     self.accel_midiout.send_message([175 + self.config.get('midi_channel'), 
    #                                 123,
    #                                 0])
