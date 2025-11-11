# host/core/platemanager.py

class PlateManager:
    """
    Manages and tracks the state of a 96-well plate, including the
    contents and volume of each well.
    """
    def __init__(self, max_volume_ul: float):
        """
        Initializes the PlateManager, creating a data structure to represent
        an empty 96-well plate.

        Args:
            max_volume_ul (float): The maximum safe volume a single well can hold.
        """
        if max_volume_ul <= 0:
            raise ValueError("Maximum well volume must be a positive number.")
        
        self.max_volume_ul = max_volume_ul
        self.plate_state = {}
        self._initialize_plate()

    def _initialize_plate(self):
        """
        Populates the plate_state dictionary with 96 empty wells and a
        placeholder for the waste location.
        """
        rows = "ABCDEFGH"
        columns = range(1, 13)
        
        empty_well_contents = {"p1": 0, "p2": 0, "p3": 0, "p4": 0}

        for row in rows:
            for col in columns:
                well_id = f"{row}{col}"
                self.plate_state[well_id] = empty_well_contents.copy()
        
        self.plate_state['waste'] = {}

    def get_well_volume(self, well_designation: str) -> float:
        """
        Calculates the total volume of liquid in a specified well.

        Args:
            well_designation (str): The ID of the well (e.g., "A1", "H12").

        Returns:
            float: The total volume in the well.
        
        Raises:
            ValueError: If the well_designation is invalid.
        """
        well = self.plate_state.get(well_designation.upper())
        if well is None or well_designation.upper() == 'WASTE':
            raise ValueError(f"Invalid well designation: '{well_designation}'")
            
        return sum(well.values())

    def is_well_empty(self, well_designation: str) -> bool:
        """
        Checks if a specific well is empty (total volume is zero).

        Args:
            well_designation (str): The ID of the well (e.g., "A1", "H12").

        Returns:
            bool: True if the well is empty, False otherwise.
        """
        try:
            return self.get_well_volume(well_designation) == 0
        except ValueError:
            return False

    def has_capacity_for(self, well_designation: str, volume_to_add: float) -> bool:
        """
        Checks if a specified volume can be added to a well without exceeding
        the plate's maximum well volume.

        Args:
            well_designation (str): The well to check.
            volume_to_add (float): The amount of liquid that is planned to be added.

        Returns:
            bool: True if the well has capacity, False otherwise.
        """
        well_id = well_designation.upper()
        if well_id not in self.plate_state or well_id == 'WASTE':
            return False # Cannot add volume to a non-existent or waste well.

        current_volume = self.get_well_volume(well_id)
        
        # Return False if the addition would cause an overflow
        if current_volume + volume_to_add > self.max_volume_ul:
            return False

        return True

    def add_liquid(self, well_designation: str, pump_id: str, volume: float):
        """
        Updates the state of a well by adding a specified volume from a pump.
        NOTE: This method does NOT check for overflow. Use has_capacity_for() first.

        Args:
            well_designation (str): The well to update.
            pump_id (str): The pump the liquid is from (e.g., "p1", "p2").
            volume (float): The volume to add.
        
        Raises:
            ValueError: If the well or pump ID is invalid.
        """
        well = self.plate_state.get(well_designation.upper())
        if well is None or well_designation.upper() == 'WASTE':
            raise ValueError(f"Invalid well designation: '{well_designation}'")

        if pump_id not in well:
            raise ValueError(f"Invalid pump ID: '{pump_id}'. Must be one of {list(well.keys())}")
            
        well[pump_id] += volume

    def find_empty_well(self) -> str | None:
        """
        Finds the first available empty well, scanning in standard order (A1, A2...).

        Returns:
            str: The designation of the first empty well found.
            None: If the entire plate is full.
        """
        rows = "ABCDEFGH"
        columns = range(1, 13)
        for row in rows:
            for col in columns:
                well_id = f"{row}{col}"
                if self.is_well_empty(well_id):
                    return well_id
        return None

if __name__ == "__main__":
    print("--- Testing PlateManager Class ---")
    
    # 1. Initialize the manager with a max volume
    MAX_VOL = 250
    pm = PlateManager(max_volume_ul=MAX_VOL)
    print(f"Initialized a plate with max well volume of {MAX_VOL} uL.")

    # 2. Test initial state and capacity checks
    print(f"\nIs well C3 empty? -> {pm.is_well_empty('C3')}")
    print(f"Does C3 have capacity for 150 uL? -> {pm.has_capacity_for('C3', 150)}")
    print(f"Does C3 have capacity for 300 uL? -> {pm.has_capacity_for('C3', 300)}")

    # 3. Add some liquid and re-check capacity
    print("\nAdding 200 uL from p1 to well C3...")
    pm.add_liquid('C3', 'p1', 200)
    print(f"Volume in C3: {pm.get_well_volume('C3')} uL")
    print(f"Does C3 have capacity for 60 uL? -> {pm.has_capacity_for('C3', 60)}") # Should be False
    print(f"Does C3 have capacity for 50 uL? -> {pm.has_capacity_for('C3', 50)}") # Should be True

    # 4. Find the next empty well
    print(f"\nFinding the first empty well...")
    first_empty = pm.find_empty_well()
    print(f"First empty well is: {first_empty}")