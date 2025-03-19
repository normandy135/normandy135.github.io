import random
import json
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import pprint
import xml.etree.ElementTree as ET
import re


USE_ROS = True  # Set to False if you want to use the hardcoded examples
unit_entries = []
leaders_mapping = {}
unit_name_counts = {}  # Track duplicate unit names
TARGET_ROS_FILE = None

if USE_ROS:
    from tkinter import Tk
    from tkinter.filedialog import askopenfilename

    Tk().withdraw()
    ros_file_path = TARGET_ROS_FILE if TARGET_ROS_FILE else askopenfilename(title="Select your Army Roster ROS", filetypes=[("ROS files", "*.ros")])

    if ros_file_path:
        tree = ET.parse(ros_file_path)
        root = tree.getroot()
    
        # Extract namespace
        namespace = {'bs': root.tag.split('}')[0].strip('{')}

        forces = root.findall('.//bs:force', namespace)
        
        # Extract Total_Points
        total_points = 0
        cost_limits = root.findall('.//bs:costLimit', namespace)
        for cost in cost_limits:
            if cost.get('name') == 'pts':
                Total_Points = int(float(cost.get('value', 0)))
                print(f"Total Points extracted: {Total_Points}")
                continue

        # Now continue extracting units
        for force in forces:
            selections = force.findall('./bs:selections/bs:selection', namespace)
            for unit in selections:
                unit_name = unit.get('name', '')
                if unit_name in ["Show/Hide Options", "Detachment"]:
                    continue

                # Count duplicates and create unique name
                unit_name_counts[unit_name] = unit_name_counts.get(unit_name, 0) + 1
                unique_unit_name = f"{unit_name} ({unit_name_counts[unit_name]})"

                base_points = 0
                costs = unit.findall('./bs:costs/bs:cost', namespace)
                for cost in costs:
                    if cost.get('name') == 'pts':
                        base_points += int(float(cost.get('value', 0)))

                upgrade_points = 0
                sub_selections = unit.findall('./bs:selections/bs:selection', namespace)
                for sub in sub_selections:
                    sub_costs = sub.findall('./bs:costs/bs:cost', namespace)
                    for cost in sub_costs:
                        if cost.get('name') == 'pts':
                            upgrade_points += int(float(cost.get('value', 0)))

                unit_total_points = base_points + upgrade_points
                unit_entries.append((unique_unit_name, unit_total_points))

                # Extract abilities
                abilities = unit.findall('./bs:profiles/bs:profile', namespace)
                for ability in abilities:
                    if ability.get('name') == 'Leader':
                        description_elem = ability.find('./bs:characteristics/bs:characteristic', namespace)
                        if description_elem is not None:
                            description = description_elem.text or ''
                            if "This model can be attached to the following unit" in description:
                                leads_units = [line.replace('-', '').strip() for line in description.split('\n') if '-' in line]
                                leaders_mapping[unique_unit_name] = leads_units
else:
    unit_entries = [
    #("Warlord", 100),
    #("Broodlord ", 80),
    #(Genestealers Warlord", 150),
    #("Genestealers Broodlord", 150),
    #("Neurolictor with XP", 80),
    #("Neurolictor with no XP", 80),
    #("Tyranid Warriors with Ranged Bio-Weapons Black", 65),
    #("Tyranid Warriors with Ranged Bio-Weapons Gray", 65),
    #("Von Ryan's Leapers 1", 140),
    #("Mawloc", 145),
    #("Trygon 2", 140),
    #("Tryannofex 1", 200),
]

def sort_into_groups(entries):
    leader_assigned = set()
    led_units_assigned = set()

    base_wave, wave_2, wave_3 = [], [], []
    base_wave_sum = wave_2_sum = wave_3_sum = 0

    half_total = Total_Points // 2
    base_wave_options = [half_total, half_total + 100, half_total - 100]
    base_wave_target = random.choice(base_wave_options)

    remaining_entries = entries[:]

    # Prioritize Character-tagged units (leaders)
    led_units_assigned = set()
    valid_leader_pairs = []

    # First, collect valid leader-led pairs
    for entry in remaining_entries[:]:
        if entry[0] in leaders_mapping and entry[0] not in leader_assigned:
            for led_unit in leaders_mapping[entry[0]]:
                

                def normalize_name(name):
                    # Lowercase
                    name = name.lower()
                    # Remove anything in parentheses
                    name = re.sub(r'\(.*?\)', '', name)
                    # Remove extra whitespace
                    #print(name)
                    return name.strip()
                    
                        
                match = next(
                    (e for e in remaining_entries
                    if normalize_name(led_unit) in normalize_name(e[0]) and e[0] not in led_units_assigned),
                    None)
                if match:
                    valid_leader_pairs.append((entry, match))
                    #print(entry)
                    #print(match)
                    leader_assigned.add(entry[0])
                    led_units_assigned.add(match[0])
                    break

    # Randomly assign each leader pair to a wave
    for leader, led in valid_leader_pairs:
        target_wave = random.choice(['base', 'wave2', 'wave3'])
        if target_wave == 'base' and base_wave_sum + leader[1] + led[1] <= base_wave_target:
            base_wave.append(leader)
            base_wave.append(led)
            base_wave_sum += leader[1] + led[1]
        elif target_wave == 'wave2' and wave_2_sum + wave_3_sum + leader[1] + led[1] <= Total_Points - base_wave_sum:
            wave_2.append(leader)
            wave_2.append(led)
            wave_2_sum += leader[1] + led[1]
        elif target_wave == 'wave3' and wave_3_sum + wave_2_sum + leader[1] + led[1] <= Total_Points - base_wave_sum:
            wave_3.append(leader)
            wave_3.append(led)
            wave_3_sum += leader[1] + led[1]
        else:
            # If target wave overflows, fallback to any wave with space
            if base_wave_sum + leader[1] + led[1] <= base_wave_target:
                base_wave.append(leader)
                base_wave.append(led)
                base_wave_sum += leader[1] + led[1]
            elif wave_2_sum <= wave_3_sum and wave_2_sum + wave_3_sum + leader[1] + led[1] <= Total_Points - base_wave_sum:
                wave_2.append(leader)
                wave_2.append(led)
                wave_2_sum += leader[1] + led[1]
            elif wave_3_sum + wave_2_sum + leader[1] + led[1] <= Total_Points - base_wave_sum:
                wave_3.append(leader)
                wave_3.append(led)
                wave_3_sum += leader[1] + led[1]

        remaining_entries.remove(leader)
        remaining_entries.remove(led)

    # Shuffle remaining entries
    random.shuffle(remaining_entries)

    # Assign remaining entries randomly
    for entry in remaining_entries[:]:
        if base_wave_sum + entry[1] <= base_wave_target:
            base_wave.append(entry)
            base_wave_sum += entry[1]
            remaining_entries.remove(entry)   

    remaining_target = Total_Points - base_wave_sum

 # 1) Calculate the Wave 2 + Wave 3 target & tolerance
    wave_2_3_target = Total_Points - base_wave_sum
    average_target = wave_2_3_target / 2
    tolerance = int(average_target * 0.10)

    for entry in remaining_entries[:]:
        if wave_2_sum <= wave_3_sum and wave_2_sum + wave_3_sum + entry[1] <= remaining_target:
            wave_2.append(entry)
            wave_2_sum += entry[1]
            remaining_entries.remove(entry)
        elif wave_3_sum + wave_2_sum + entry[1] <= remaining_target:
            wave_3.append(entry)
            wave_3_sum += entry[1]
            remaining_entries.remove(entry)
        wave_2_3_target = Total_Points - base_wave_sum
        #print(base_wave_sum)
        #print(wave_2_sum)
        #print(wave_3_sum)
        wave_2_3_average = wave_2_3_target / 2
        individual_tolerance = int(wave_2_3_average * 0.10)
        #print(individual_tolerance)
    if abs(wave_2_sum - wave_3_sum) > individual_tolerance:
        return None  # Retry if imbalance exceeds 10%
    

    combined_waves_total = wave_2_sum + wave_3_sum

    total_used = base_wave_sum + wave_2_sum + wave_3_sum
    #if abs(combined_waves_total - wave_2_3_target) > tolerance:
        # If not within the allowed fluctuation, discard this result (forces a retry)
    #    return None

    gap = abs(Total_Points - total_used)

    return {
        "The Base Wave": base_wave,
        "Wave 2": wave_2,
        "Wave 3": wave_3,
        "Total Points Used": total_used,
        "Gap": gap
    }


def is_base_wave_different(all_prev_waves, new_wave):
    new_set = set(name for name, _ in new_wave)
    for prev_wave in all_prev_waves:
        prev_set = set(name for name, _ in prev_wave)
        difference = len(new_set.symmetric_difference(prev_set))
        if difference < len(prev_set) // 2:
            return False
    return True


def is_wave_different(all_prev_waves, new_wave, threshold=0.25):
    new_set = set(name for name, _ in new_wave)
    for prev_wave in all_prev_waves:
        prev_set = set(name for name, _ in prev_wave)
        difference = len(new_set.symmetric_difference(prev_set))
        if difference < max(1, int(len(prev_set) * threshold)):
            return False
    return True


roster_points = sum(points for _, points in unit_entries)
print()
print(f"Total Points Set: {Total_Points}")
print("Leaders and the units they can lead:")
for leader, units in leaders_mapping.items():
     print(f"{leader} leads: {', '.join(units)}")
print(f"Roster Points: {roster_points}")

print()
results = []
attempts = 0
max_attempts = 800
previous_base_waves, previous_wave_2s, previous_wave_3s = [], [], []

all_valid_results = []

while len(results) < 50 and attempts < max_attempts:  # Main loop
    random.shuffle(unit_entries)
    result = sort_into_groups(unit_entries)


    if result is None:
        continue

    total_used_points = sum(
        points for group in [result["The Base Wave"], result["Wave 2"], result["Wave 3"]] for _, points in group
    )

    base_wave_ok = not previous_base_waves or is_base_wave_different(previous_base_waves, result["The Base Wave"])
    wave2_ok = not previous_wave_2s or is_wave_different(previous_wave_2s, result["Wave 2"])
    wave3_ok = not previous_wave_3s or is_wave_different(previous_wave_3s, result["Wave 3"])

    base_wave_total = sum(points for _, points in result["The Base Wave"])
    wave_2_3_total = sum(points for _, points in result["Wave 2"]) + sum(points for _, points in result["Wave 3"])
    tolerance = int(0.1 * base_wave_total)
    within_10_percent = abs(wave_2_3_total - base_wave_total) <= tolerance

    if total_used_points <= Total_Points and base_wave_ok and wave2_ok and wave3_ok and within_10_percent:
        dist_tuple = (
            tuple(sorted(result["The Base Wave"])),
            tuple(sorted(result["Wave 2"])),
            tuple(sorted(result["Wave 3"]))
        )
        if dist_tuple not in results:
            results.append(dist_tuple)
            all_valid_results.append(result)
            previous_base_waves.append(result["The Base Wave"])
            previous_wave_2s.append(result["Wave 2"])
            previous_wave_3s.append(result["Wave 3"])
    attempts += 1

# Sort and print results by gap
all_valid_results.sort(key=lambda x: x["Gap"])

for idx, result in enumerate(all_valid_results):
    print("=" * 60)
    for wave, units in result.items():
        if isinstance(units, list):
            unit_list = ', '.join(f"{name} ({points} pts)" for name, points in units)
            total_wave_points = sum(points for _, points in units)
            print(f"{wave} (Total: {total_wave_points} pts): {unit_list}")
    print()
    print(f"Missing Points: {result['Gap']} pts")
    unplaced_units = set(name for name, _ in unit_entries) - set(name for wave in [result['The Base Wave'], result['Wave 2'], result['Wave 3']] for name, _ in wave)
    if unplaced_units:
        print("Unplaced Units:", ', '.join(unplaced_units))
    print("=" * 60)
    

if len(results) < 5:
    print("Fewer than 5 unique distributions found. Adjust points or units.")

# Show results in output window
def show_output_window(results):
    window = tk.Tk()
    window.title("Army Distribution Results")

    # Make window resizable and text area fill the window
    text_area = ScrolledText(window, wrap=tk.WORD, font=("Consolas", 10))
    text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Insert summary at the top
    text_area.insert(tk.END, f"Total Points: {Total_Points} pts")

    for idx, result in enumerate(results):
        text_area.insert(tk.END, "=" * 60 + "")
        for wave, units in result.items():
            if isinstance(units, list):
                unit_list = ', '.join(f"{name} ({points} pts)" for name, points in units)
                total_wave_points = sum(points for _, points in units)
                text_area.insert(tk.END, f"{wave} (Total: {total_wave_points} pts):{unit_list}")
        text_area.insert(tk.END, f"Missing Points: {result['Gap']} pts")
        text_area.insert(tk.END, "=" * 60 + "")

    text_area.config(state=tk.DISABLED)
    window.mainloop()

show_output_window(all_valid_results)
