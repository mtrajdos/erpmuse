"""Vector-based pseudo-random sequence controller"""
import random
from datetime import datetime
from pathlib import Path
from kivy.logger import Logger
import session
from kivy.utils import platform as kivy_platform
import os


class VectorSequenceController:
    """Creates and manages pseudo-random stimulus sequences using category vectors"""
    
    def __init__(self, config):
        self.config = config

        if kivy_platform in ('android', 'ios'):
            self.vector_dir = Path("/storage/emulated/0/Download/vectors")
        else:
            self.vector_dir = Path(os.path.join(os.getcwd(), "vectors"))
            
        self.vector_dir.mkdir(parents=True, exist_ok=True)
        
        self.category_sequence = []
        self.current_vector_file = None
    
    def load_or_create_vector(self, total_stimuli=5000):
        """
        Load existing vector file or create new one if not available.
        
        Returns:
            List of category names in presentation order
        """
        # Check for existing vector files
        existing_vectors = list(self.vector_dir.glob("VECTOR-*-STIMULI-*.txt"))
        
        if existing_vectors:
            # Use most recent vector file
            vector_file = sorted(existing_vectors)[-1]
            Logger.info(f"Loading existing vector: {vector_file.name}")
            self.category_sequence = self._load_vector_file(vector_file)
        else:
            # Create new vector
            Logger.info(f"No vector file found. Creating new vector with {total_stimuli} stimuli")
            self.category_sequence = self._create_vector_sequence(total_stimuli)
            self._save_vector_file(self.category_sequence, total_stimuli)
        
        return self.category_sequence
    
    def _create_vector_sequence(self, total_stimuli):
        """Create pseudo-random sequence with max 3 consecutive same categories"""
        categories = self.config.CATEGORIES
        num_categories = len(categories)
        
        # Ensure equal distribution
        if total_stimuli % num_categories != 0:
            total_stimuli = (total_stimuli // num_categories) * num_categories
            Logger.warning(f"Adjusted total to {total_stimuli} for equal distribution")
        
        stimuli_per_category = total_stimuli // num_categories
        
        # Create pool with equal counts
        pool = []
        for category in categories:
            pool.extend([category] * stimuli_per_category)
        
        # Shuffle with constraint: no more than 3 consecutive
        sequence = []
        attempts = 0
        max_attempts = 100
        
        while attempts < max_attempts:
            random.shuffle(pool)
            if self._check_consecutive_constraint(pool, max_consecutive=3):
                sequence = pool
                break
            attempts += 1
        
        if not sequence:
            # Fallback: use constrained building
            sequence = self._build_constrained_sequence(pool)
        
        return sequence
    
    def _check_consecutive_constraint(self, sequence, max_consecutive=3):
        """Check if sequence has no more than max_consecutive same items"""
        consecutive_count = 1
        
        for i in range(1, len(sequence)):
            if sequence[i] == sequence[i-1]:
                consecutive_count += 1
                if consecutive_count > max_consecutive:
                    return False
            else:
                consecutive_count = 1
        
        return True
    
    def _build_constrained_sequence(self, pool):
        """Build sequence ensuring no more than 3 consecutive same categories"""
        sequence = []
        remaining = pool.copy()
        random.shuffle(remaining)
        
        while remaining:
            # Pick next item
            if len(sequence) < 3:
                # Just add it
                item = remaining.pop(0)
                sequence.append(item)
            else:
                # Check if we need to avoid same category
                last_three = sequence[-3:]
                if len(set(last_three)) == 1:  # All same
                    # Find different category
                    found = False
                    for i, item in enumerate(remaining):
                        if item != last_three[0]:
                            sequence.append(remaining.pop(i))
                            found = True
                            break
                    
                    if not found:
                        # No choice, add anyway
                        sequence.append(remaining.pop(0))
                else:
                    # Safe to add any
                    sequence.append(remaining.pop(0))
        
        return sequence
    
    def _save_vector_file(self, sequence, total_stimuli):
        """Save vector sequence to file"""
        timestamp = session.SESSION_TIMESTAMP
        filename = f"VECTOR-{total_stimuli}-STIMULI-{timestamp}.txt"
        filepath = self.vector_dir / filename
        
        # Calculate category counts
        category_counts = {cat: sequence.count(cat) for cat in self.config.CATEGORIES}
        
        with open(filepath, 'w') as f:
            # Header
            f.write(f"Created: {timestamp}\n\n")
            
            # Category counts
            for category in self.config.CATEGORIES:
                count = category_counts.get(category, 0)
                f.write(f"n {category}: {count}\n")
            f.write("\n")
            
            # Sequence
            for category in sequence:
                f.write(f"{category}\n")
        
        self.current_vector_file = filepath
        Logger.info(f"Saved vector to: {filepath}")
    
    def _load_vector_file(self, filepath):
        """Load vector sequence from file"""
        sequence = []
        
        with open(filepath, 'r') as f:
            lines = f.readlines()
            
            # Skip header and find start of sequence
            in_sequence = False
            for line in lines:
                line = line.strip()
                
                # Empty line after counts marks start of sequence
                if not line and not in_sequence:
                    # Check if we've passed the counts section
                    for prev_line in lines[:lines.index(line + '\n')]:
                        if 'n ' in prev_line:
                            in_sequence = True
                            break
                
                # Read sequence entries
                elif in_sequence and line in self.config.CATEGORIES:
                    sequence.append(line)
        
        self.current_vector_file = filepath
        Logger.info(f"Loaded {len(sequence)} categories from vector")
        return sequence