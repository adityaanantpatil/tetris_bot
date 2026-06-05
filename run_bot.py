import cv2
import numpy as np
import mss
import pydirectinput
import time
import os

# --- 1. CONFIGURATION ---
# (Using your precise calibration!)
BBOX_COORDINATES = {'top': 444, 'left': 1179, 'width': 522, 'height': 1045}

KEY_LEFT = 'left'
KEY_RIGHT = 'right'
KEY_ROTATE_CW = 'up'
KEY_HARD_DROP = 'space'

pydirectinput.PAUSE = 0.01 

# --- 2. THE TETRIS PHYSICS ENGINE (From Colab) ---
SHAPES = {
    'O': [[[0,0], [0,1], [1,0], [1,1]]],
    'I': [[[0,0], [0,1], [0,2], [0,3]], [[0,0], [1,0], [2,0], [3,0]]],
    'Z': [[[0,0], [0,1], [1,1], [1,2]], [[0,1], [1,0], [1,1], [2,0]]],
    'S': [[[0,1], [0,2], [1,0], [1,1]], [[0,0], [1,0], [1,1], [2,1]]],
    'J': [[[0,0], [1,0], [1,1], [1,2]], [[0,1], [0,2], [1,0], [2,0]], [[0,0], [0,1], [0,2], [1,2]], [[0,1], [1,1], [2,0], [2,1]]],
    'L': [[[0,2], [1,0], [1,1], [1,2]], [[0,0], [1,0], [2,0], [2,1]], [[0,0], [0,1], [0,2], [1,0]], [[0,0], [0,1], [1,1], [2,1]]],
    'T': [[[0,1], [1,0], [1,1], [1,2]], [[0,0], [1,0], [1,1], [2,0]], [[0,0], [0,1], [0,2], [1,1]], [[0,1], [1,0], [1,1], [2,1]]]
}

def check_collision(board, shape, row_offset, col_offset):
    for r, c in shape:
        row = r + row_offset
        col = c + col_offset
        if row >= 20 or col < 0 or col >= 10 or board[row, col] != 0:
            return True
    return False

def drop_piece(board, shape, col_offset):
    row_offset = 0
    while not check_collision(board, shape, row_offset + 1, col_offset):
        row_offset += 1
    
    if row_offset == 0: return None, 0
        
    new_board = np.copy(board)
    for r, c in shape:
        new_board[r + row_offset, c + col_offset] = 1
        
    lines_cleared = 0
    full_rows = np.all(new_board != 0, axis=1)
    if np.any(full_rows):
        lines_cleared = np.sum(full_rows)
        new_board = new_board[~full_rows]
        empty_rows = np.zeros((lines_cleared, 10))
        new_board = np.vstack((empty_rows, new_board))
        
    return new_board, lines_cleared

def get_all_possible_states(board, piece_name):
    states = []
    rotations = SHAPES[piece_name]
    
    # We clear the top 4 rows so the falling piece doesn't block itself during simulation
    clean_board = np.copy(board)
    clean_board[0:4, :] = 0 
    
    for rotation_idx, shape in enumerate(rotations):
        max_col = max([c for r, c in shape])
        for col in range(10 - max_col):
            new_board, lines = drop_piece(clean_board, shape, col)
            if new_board is not None:
                states.append((new_board, lines, rotation_idx, col))
    return states

# --- 3. VISION & PIECE DETECTION ---
def capture_board(sct):
    screenshot = np.array(sct.grab(BBOX_COORDINATES))
    gray = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2GRAY)
    board = np.zeros((20, 10))
    cell_w = BBOX_COORDINATES['width'] / 10.0
    cell_h = BBOX_COORDINATES['height'] / 20.0
    
    for row in range(20):
        for col in range(10):
            center_x = int((col * cell_w) + (cell_w / 2))
            center_y = int((row * cell_h) + (cell_h / 2))
            if gray[center_y, center_x] > 50: 
                board[row, col] = 1
    return board

def detect_spawned_piece(board):
    """Scans the top 2 rows to identify the newly spawned piece."""
    spawn_area = board[0:2, 3:7]
    if np.array_equal(spawn_area, [[0,0,0,0], [1,1,1,1]]): return 'I'
    if np.array_equal(spawn_area, [[0,1,1,0], [0,1,1,0]]): return 'O'
    if np.array_equal(spawn_area, [[0,1,0,0], [1,1,1,0]]): return 'T'
    if np.array_equal(spawn_area, [[0,1,1,0], [1,1,0,0]]): return 'S'
    if np.array_equal(spawn_area, [[1,1,0,0], [0,1,1,0]]): return 'Z'
    if np.array_equal(spawn_area, [[1,0,0,0], [1,1,1,0]]): return 'J'
    if np.array_equal(spawn_area, [[0,0,1,0], [1,1,1,0]]): return 'L'
    return None

# --- 4. THE BRAIN ---
def get_board_metrics(board):
    mask = board != 0
    heights = np.where(mask.any(axis=0), board.shape[0] - np.argmax(mask, axis=0), 0)
    aggregate_height = np.sum(heights)
    bumpiness = np.sum(np.abs(np.diff(heights)))
    holes_matrix = (np.cumsum(mask, axis=0) > 0) & (board == 0)
    holes = np.sum(holes_matrix)
    return aggregate_height, holes, bumpiness

def calculate_move_score(board, lines_cleared, weights):
    w_lines, w_height, w_holes, w_bumpiness = weights
    aggregate_height, holes, bumpiness = get_board_metrics(board)
    return (w_lines * lines_cleared) + (w_height * aggregate_height) + (w_holes * holes) + (w_bumpiness * bumpiness)

# --- 5. EXECUTION ---
# --- 5. EXECUTION ---
def execute_move(rotations, translations):
    """Fires keystrokes with a safer delay so the browser doesn't drop inputs."""
    PRESS_DELAY = 0.03 # 30ms ensures the browser engine registers every tap
    
    # 1. Rotate
    for _ in range(rotations):
        pydirectinput.press(KEY_ROTATE_CW)
        time.sleep(PRESS_DELAY)
        
    # 2. Translate Left/Right
    if translations < 0:
        for _ in range(abs(translations)):
            pydirectinput.press(KEY_LEFT)
            time.sleep(PRESS_DELAY)
    elif translations > 0:
        for _ in range(translations):
            pydirectinput.press(KEY_RIGHT)
            time.sleep(PRESS_DELAY)
            
    # 3. Hard Drop
    time.sleep(0.03) 
    pydirectinput.press(KEY_HARD_DROP)

# --- 6. MAIN LOOP ---
def main():
    # [Lines, Height, Holes, Bumpiness]
    weights = np.array([0.760, -0.510, -0.356, -0.184])
    print(f"🧠 Brain running with baseline El-Tetris weights: {weights}")
    print("🚀 Bot starting in 3 seconds. Click into the TETR.IO window!")
    time.sleep(3)
    
    # This maps exactly where the leftmost block of a piece ends up 
    # based on how many times you pressed 'Rotate CW'. (Eliminates drift!)
    NATURAL_SPAWN_COL = {
        'O': [4],
        'I': [3, 5],
        'Z': [3, 4],
        'S': [3, 4],
        'J': [3, 4, 3, 3],
        'L': [3, 4, 3, 3],
        'T': [3, 4, 3, 3]
    }
    
    with mss.MSS() as sct:
        waiting_for_new_piece = True
        
        while True:
            current_board = capture_board(sct)
            spawned_piece = detect_spawned_piece(current_board)
            
            if spawned_piece and waiting_for_new_piece:
                possible_states = get_all_possible_states(current_board, spawned_piece)
                
                if possible_states:
                    best_score = -float('inf')
                    best_rot = 0
                    best_col = 0
                    
                    for simulated_board, lines, rot, col in possible_states:
                        score = calculate_move_score(simulated_board, lines, weights)
                        if score > best_score:
                            best_score = score
                            best_rot = rot
                            best_col = col
                    
                    # Look up where the piece currently is in the real game after rotation
                    current_real_col = NATURAL_SPAWN_COL[spawned_piece][best_rot]
                    
                    # Calculate how many keys to press from that exact starting point
                    target_translations = best_col - current_real_col
                    
                    execute_move(best_rot, target_translations)
                    waiting_for_new_piece = False 
            
            elif not spawned_piece:
                waiting_for_new_piece = True
                
            time.sleep(0.01)

if __name__ == "__main__":
    main()