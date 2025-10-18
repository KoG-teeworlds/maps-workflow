import pandas as pd
import os

def get_stars_5_scale(star_value):
    # Converts a number into a 5-star rating string.
    star_value = str(star_value)
    if star_value == '1':
        return '★☆☆☆☆'
    elif star_value == '2':
        return '★★☆☆☆'
    elif star_value == '3':
        return '★★☆☆☆'
    elif star_value == '4':
        return '★★★★☆'
    elif star_value == '5':
        return '★★★★★'
    else: # To prevent bugs
        return '☆☆☆☆☆'
    
def get_stars_4_scale(star_value):
    # Converts a number into a 4-star rating string.
    star_value = str(star_value)
    if star_value == '1':
        return '★☆☆☆'
    elif star_value == '2':
        return '★★☆☆'
    elif star_value == '3':
        return '★★☆☆'
    elif star_value == '4':
        return '★★★★'
    else: # To prevent bugs
        return '☆☆☆☆'

def get_stars_3_scale(star_value):
    # Converts a number into a 3-star rating string.
    star_value = str(star_value)
    if star_value == '1':
        return '★☆☆'
    elif star_value == '2':
        return '★★☆'
    elif star_value == '3':
        return '★★☆'
    else: # To prevent bugs
        return '☆☆☆'

def get_group_name(length):
    # Finds the group name for a given map length.
    length_groups = {
        "Short Maps": ['XXS', 'XS'],
        "Medium Maps": ['S', 'M'],
        "Long Maps": ['L', 'XL'],
        "Very Long Maps": ['XXL', 'XXXL', 'WTF'],
        "Other Maps": ['N/A']
    }
    for group, lengths in length_groups.items():
        if length in lengths:
            return group
    return "Other Maps"

def truncate_display_name(map_name, mapper):
    # Checks if 'map_name by mapper' is over 31 chars.
    limit = 31
    base_text = f"{map_name}{mapper}"
    
    if len(base_text) > limit:
        # Calculate the maximum allowed length for the mapper's name
        max_mapper_len = limit - len(base_text)
        return mapper[:max_mapper_len]
    return mapper

def generate_vote_file(df, difficulty):
    # Generates a .cfg file for a given difficulty.
    print(f"Processing difficulty: {difficulty}...")
    
    difficulty_maps = df[df['difficulty'] == difficulty].copy()

    if difficulty_maps.empty:
        print(f" -> No maps found for '{difficulty}'. Skipping.")
        return

    # Counter to make each blank vote unique
    blank_vote_counter = 1
    
    output_lines = [f'add_vote "{" " * blank_vote_counter}" "info"']
    blank_vote_counter += 1

    # --- Conditional logic for sorting and formatting ---
    if difficulty in ['MOD', 'SOL']:
        maps_sorted = difficulty_maps.sort_values('map_name')
        output_lines.append(f'add_vote "__________ {difficulty} Maps __________" "info"')
        
        for _, row in maps_sorted.iterrows():

            map_name = row["map_name"]
            mappers = row["mappers"]
            # Truncate mapper name if necessary
            mapper = truncate_display_name(map_name, mappers)
            
            vote_string = f'add_vote "{map_name} by {mapper} | {get_stars_5_scale(row["stars"])} | {row["points"]} pts" "change_map \\"{row["map_name"]}\\""'
            output_lines.append(vote_string)
            
    # For all other standard difficulties
    else:
        difficulty_maps['length'] = difficulty_maps['length'].fillna('N/A')
        length_order = ['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL', 'WTF', 'N/A']
        difficulty_maps['length'] = pd.Categorical(difficulty_maps['length'], categories=length_order, ordered=True)
        maps_sorted = difficulty_maps.sort_values('length')
        
        current_group = ""
        for _, row in maps_sorted.iterrows():
            group_name = get_group_name(row['length'])
            if group_name != current_group:
                # This block adds a blank vote between categories
                if current_group:
                    output_lines.append(f'add_vote "{" " * blank_vote_counter}" "info"')
                    blank_vote_counter += 1
                
                current_group = group_name
                output_lines.append(f'add_vote "__________ {current_group} __________" "info"')
            
            map_name = row["map_name"]
            mappers = row["mappers"]
            # Truncate mapper name if necessary
            mapper = truncate_display_name(map_name, mappers)

            # Use 4 stars for EXT, 3 for others
            if difficulty == 'EXT':
                stars_display = get_stars_4_scale(row["stars"])
            else:
                stars_display = get_stars_3_scale(row["stars"])

            vote_string = f'add_vote "{map_name} by {mapper} | {stars_display} | {row["length"]} | {row["points"]} pts" "change_map \\"{row["map_name"]}\\""'
            output_lines.append(vote_string)
        blank_vote_counter = 2

    output_lines.append('add_vote "        " "info"')

     # Output in 'votes' folder
    file_name = f"votes_{difficulty.lower()}.cfg"
    output_path = os.path.join('votes', file_name)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
        
    print(f" -> ✅ Successfully created vote menu: {output_path}")


# ---  Main Function ---
def generate_votes():

    try:
        main_df = pd.read_csv('kog_maps.csv')
        os.makedirs('votes', exist_ok=True)

        difficulties_to_process = ['SOL', 'ESY', 'MN', 'HRD', 'INS', 'EXT', 'MOD']
        
        for diff in difficulties_to_process:
            generate_vote_file(main_df, diff)
            print("-" * 20)

        print("\nAll vote menus have been generated in the 'votes' folder.")

    except FileNotFoundError:
        print("Error: 'kog_maps.csv' not found. Make sure the file is in the same directory as the script.")


if __name__ == "__main__":
    generate_votes()