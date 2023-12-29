#!/bin/bash

#aconnect 36:0 128:0 # Connect Keystep Pro to FluidSynth
#aconnect 36:0 24:0  # Connect Keystep Pro to U6MIDI Pro
#aconnect 40:0 24:0  # Connect Novation Launchpad Pro MK3 to U6MIDI Pro

#!/bin/bash

get_client_id() {
    local device_name="$1"
    aconnect -l | grep "client.*${device_name}" | awk '{print $2}' | sed 's/://'
}

# Get client IDs
key_step_pro_id=$(get_client_id "KeyStep Pro")
u6midi_pro_id=$(get_client_id "U6MIDI Pro")
launchpad_pro_mk3_id=$(get_client_id "Launchpad Pro MK3")
fluid_synth_id=$(get_client_id "FLUID Synth")

echo "KeyStep Pro ID: $key_step_pro_id"
echo "U6MIDI Pro ID: $u6midi_pro_id"
echo "Launchpad Pro MK3 ID: $launchpad_pro_mk3_id"
echo "Fluid Synth ID: $fluid_synth_id"

# Connect KeyStep Pro to FluidSynth and U6MIDI Pro
if [[ -n $key_step_pro_id && -n $u6midi_pro_id && -n $fluid_synth_id ]]; then
    aconnect $key_step_pro_id:0 $fluid_synth_id:0
    aconnect $key_step_pro_id:0 $u6midi_pro_id:0
fi

# Connect Novation Launchpad Pro MK3 to U6MIDI Pro
if [[ -n $launchpad_pro_mk3_id && -n $u6midi_pro_id ]]; then
    aconnect $launchpad_pro_mk3_id:0 $u6midi_pro_id:0
fi

