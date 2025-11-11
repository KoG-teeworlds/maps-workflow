import polars as pl
import os
from typing import Dict, Any, List

def get_stars(value: str, max_stars: int) -> str:
    FILLED_STAR = '★'
    EMPTY_STAR = '☆'
    
    try:
        # Clean the input string
        filled_count = int(value.strip('+'))
    except (ValueError, AttributeError):
        filled_count = 0
        
    filled_count = min(filled_count, max_stars)
    
    empty_count = max_stars - filled_count
    
    return FILLED_STAR * filled_count + EMPTY_STAR * empty_count


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


def generate_vote_file(df: pl.DataFrame, difficulty: str):
    print(f"Processing difficulty: {difficulty}...")
    
    difficulty_maps = df.filter(pl.col('difficulty') == difficulty)

    if difficulty_maps.is_empty():
        print(f" -> No maps found for '{difficulty}'. Skipping.")
        return

    blank_vote_counter = 1
    output_lines = [f'add_vote "{" " * blank_vote_counter}" "info"']
    blank_vote_counter += 1

    if difficulty in ['MOD', 'SOL']:
        maps_sorted = difficulty_maps.sort('map_name')
        output_lines.append(f'add_vote "__________ {difficulty} Maps __________" "info"')
        
        for row in maps_sorted.to_dicts():
            map_name = row["map_name"]
            mappers = row["mappers"]
            mapper = truncate_display_name(map_name, mappers)
            
            stars_display = get_stars(row["stars"], 5)
            
            vote_string = f'add_vote "{map_name} by {mapper} | {stars_display} | {row["points"]} pts" "change_map \\"{row["map_name"]}\\""'
            output_lines.append(vote_string)
            
    else:
        length_order = ['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL', 'WTF', 'N/A']
        
        rank_expression = pl.when(pl.col('length') == length_order[0]).then(pl.lit(0))
        
        for rank, length in enumerate(length_order[1:], start=1):
             rank_expression = rank_expression.when(pl.col('length') == length).then(pl.lit(rank))
        
        rank_expression = rank_expression.otherwise(pl.lit(99)).alias('length_rank')
        
        maps_sorted = (
            difficulty_maps
            .with_columns(pl.col('length').fill_null('N/A'))
            .with_columns(rank_expression)
            .sort('length_rank')
            .drop('length_rank')
        )
        
        current_group = ""
        for row in maps_sorted.to_dicts():
            group_name = get_group_name(row['length'])
            if group_name != current_group:
                if current_group:
                    output_lines.append(f'add_vote "{" " * blank_vote_counter}" "info"')
                    blank_vote_counter += 1
                
                current_group = group_name
                output_lines.append(f'add_vote "__________ {current_group} __________" "info"')
            
            map_name = row["map_name"]
            mappers = row["mappers"]
            mapper = truncate_display_name(map_name, mappers)


            if difficulty == 'EXT':
                stars_display = get_stars(row["stars"], 4)
            else:
                stars_display = get_stars(row["stars"], 3)
            
            vote_string = f'add_vote "{map_name} by {mapper} | {stars_display} | {row["length"]} | {row["points"]} pts" "change_map \\"{row["map_name"]}\\""'
            output_lines.append(vote_string)
        blank_vote_counter = 2

    output_lines.append('add_vote "       " "info"')

    file_name = f"votes_{difficulty.lower()}.cfg"
    output_path = os.path.join('votes', file_name)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
        f.write('\n')
        
    print(f" -> ✅ Successfully created vote menu: {output_path}")


# ---  Main Function ---
def generate_votes():

    try:
        main_df = pl.read_csv(
            'kog_maps.csv', 
            schema_overrides={'stars': pl.String}, 
            quote_char=None
        )
        
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
