import cv2
import numpy as np
import mss

def calibrate_tetris_grid():
    print("Instructions:")
    print("1. Open TETR.IO in your browser and keep it visible on your screen.")
    print("2. A screenshot window will appear. Press 'Space' or 'Enter' to freeze the frame.")
    print("3. Click and drag a bounding box precisely from the TOP-LEFT corner of the first grid cell")
    print("   to the BOTTOM-RIGHT corner of the bottom row.")
    print("4. Press 'Enter' to confirm the selection. The exact coordinates will print out.")
    
    with mss.mss() as sct:
        # Capture your primary monitor layout
        monitor = sct.monitors[1]
        screenshot = np.array(sct.grab(monitor))
        # Convert from BGRA to BGR for OpenCV compatibility
        frame = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
        
        # Select Region of Interest (ROI)
        # cv2.selectROI opens a window and handles drag-and-drop bounding boxes natively
        roi = cv2.selectROI("TETR.IO Calibration - Drag over the 20x10 playfield", frame, fromCenter=False, showCrosshair=True)
        
        x, y, w, h = roi
        cv2.destroyAllWindows()
        
        if w == 0 or h == 0:
            print("❌ Calibration cancelled or invalid selection.")
            return None
            
        bounding_box = {
            "top": int(y),
            "left": int(x),
            "width": int(w),
            "height": int(h)
        }
        
        print("\n🎉 Calibration Successful! Copy these coordinates for your main bot script:")
        print("-" * 50)
        print(f"BBOX_COORDINATES = {bounding_box}")
        print("-" * 50)
        
        # Calculate cell metrics for validation
        cell_w = w / 10
        cell_h = h / 20
        print(f"Calculated Cell Dimensions: {cell_w:.2f}x{cell_h:.2f} pixels.")
        return bounding_box

if __name__ == "__main__":
    calibrate_tetris_grid()