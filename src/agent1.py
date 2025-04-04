#!/usr/bin/python3
# ^^ note the python directive on the first line
# COMP3411/9814 agent initiation file 
# requires the host to be running before the agent
# typical initiation would be (file in working directory, port = 31415)
#        python3 agent.py -p 31415
# created by Leo Hoare
# with slight modifications by Alan Blair

# Declaring visible grid to agent

import heapq
import sys
import socket

# Declaring visible grid to agent
view = [['' for _ in range(5)] for _ in range(5)]

# Global variables
mental_map = [[' ' for _ in range(20)] for _ in range(20)]  # 20x20 mental map
agent_path = []  # Tracks the agent's path for backtracking
start_pos = None  # Starting position of the agent
has_treasure = False  # Whether the agent has collected the treasure
tools = {'a': False, 'k': False, 'd': False, 'raft': False}  # Tools the agent is carrying
used_dynamite = False  # Track if dynamite has been used
obstacles_to_remove = set()  # Track obstacles that can be removed with tools
agent_global_pos = (10, 10)  # Initial position of the agent in the mental map

class AgentState:
    def __init__(self):
        self.mental_map = [[' ' for _ in range(20)] for _ in range(20)]
        self.tools = {'a': False, 'k': False, 'd': False, 'raft': False}
        self.path = []
        # ... other state variables

def transform_view_based_on_orientation(view, agent_direction):
    if agent_direction == '^':
        return view  # No transformation needed
    elif agent_direction == 'v':
        return [row[::-1] for row in view[::-1]]  # Flip vertically and horizontally
    elif agent_direction == '<':
        return [list(row) for row in zip(*view)][::-1]  # Rotate 90 degrees counterclockwise
    elif agent_direction == '>':
        return [list(row)[::-1] for row in zip(*view)]  # Rotate 90 degrees clockwise
    return view

def update_agent_global_position(agent_global_pos, agent_direction):
    x, y = agent_global_pos
    if agent_direction == '^':
        return (x - 1, y)
    elif agent_direction == 'v':
        return (x + 1, y)
    elif agent_direction == '<':
        return (x, y - 1)
    elif agent_direction == '>':
        return (x, y + 1)
    return (x, y)

def dijkstra(grid, start, targets):
    rows, cols = len(grid), len(grid[0])
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    pq = [(0, start)]
    visited = {start: 0}
    path = {}

    while pq:
        current_dist, (x, y) = heapq.heappop(pq)
        if (x, y) in targets:
            full_path = []
            while (x, y) != start:
                full_path.append((x, y))
                x, y = path[(x, y)]
            full_path.reverse()
            return full_path

        for dx, dy in directions:
            nx, ny = x + dx, y + dy

            if 0 <= nx < rows and 0 <= ny < cols:
                cell = grid[nx][ny]
                # Only consider moves that won't kill the agent
                if cell in ['a', 'k', 'd', '$', ' ', '^', 'v', '<', '>']:  # Safe moves
                    new_dist = current_dist + 1
                    if (nx, ny) not in visited or new_dist < visited[(nx, ny)]:
                        visited[(nx, ny)] = new_dist
                        heapq.heappush(pq, (new_dist, (nx, ny)))
                        path[(nx, ny)] = (x, y)
                elif cell == '~' and tools['raft']:  # Water with raft
                    new_dist = current_dist + 1
                    if (nx, ny) not in visited or new_dist < visited[(nx, ny)]:
                        visited[(nx, ny)] = new_dist
                        heapq.heappush(pq, (new_dist, (nx, ny)))
                        path[(nx, ny)] = (x, y)
                elif cell == 'T' and tools['a']:  # Tree with axe
                    new_dist = current_dist + 1
                    if (nx, ny) not in visited or new_dist < visited[(nx, ny)]:
                        visited[(nx, ny)] = new_dist
                        heapq.heappush(pq, (new_dist, (nx, ny)))
                        path[(nx, ny)] = (x, y)
                elif cell == '-' and tools['k']:  # Door with key
                    new_dist = current_dist + 1
                    if (nx, ny) not in visited or new_dist < visited[(nx, ny)]:
                        visited[(nx, ny)] = new_dist
                        heapq.heappush(pq, (new_dist, (nx, ny)))
                        path[(nx, ny)] = (x, y)
                elif cell == '*' and tools['d'] and not used_dynamite:  # Wall with unused dynamite
                    new_dist = current_dist + 1
                    if (nx, ny) not in visited or new_dist < visited[(nx, ny)]:
                        visited[(nx, ny)] = new_dist
                        heapq.heappush(pq, (new_dist, (nx, ny)))
                        path[(nx, ny)] = (x, y)

    return []

# Update the mental map based on the 5x5 view
def update_mental_map(view, agent_global_pos, agent_direction):
    transformed_view = transform_view_based_on_orientation(view, agent_direction)
    for i in range(5):
        for j in range(5):
            x = agent_global_pos[0] + i - 2
            y = agent_global_pos[1] + j - 2
            if 0 <= x < 20 and 0 <= y < 20:
                mental_map[x][y] = transformed_view[i][j]
    print("\nUpdated mental map:")
    print_mental_map()

# Get the agent's current position in the mental map
def get_agent_pos(view):
    for i in range(5):
        for j in range(5):
            if view[i][j] in ['^', 'v', '<', '>']:
                return (i, j)
    return None

# Convert 5x5 view coordinates to mental map coordinates
def local_to_global(view_pos, agent_pos):
    global_pos = (agent_pos[0] + view_pos[0] - 2, agent_pos[1] + view_pos[1] - 2)
    print(f"Converting local pos {view_pos} to global pos {global_pos} (agent at {agent_pos})")
    return global_pos

# Convert global coordinates to local coordinates relative to the agent's position
def global_to_local(global_pos, agent_global_pos):
    local_pos = (global_pos[0] - agent_global_pos[0] + 2, global_pos[1] - agent_global_pos[1] + 2)
    print(f"Converting global pos {global_pos} to local pos {local_pos} (agent at {agent_global_pos})")
    return local_pos

def can_move_forward(view, agent_local_pos):
    x, y = agent_local_pos
    if view[x][y] == '^':
        next_cell = view[x-1][y]
    elif view[x][y] == 'v':
        next_cell = view[x+1][y]
    elif view[x][y] == '<':
        next_cell = view[x][y-1]
    elif view[x][y] == '>':
        next_cell = view[x][y+1]
    else:
        return False

    # Check if the next cell is a tool and pick it up
    if next_cell in ['a', 'k', 'd', '$']:
        return True

    # Check for obstacles and use tools if available
    if next_cell == 'T' and tools['a']:  # Tree and has axe
        return 'C'  # Chop the tree
    elif next_cell == '-' and tools['k']:  # Door and has key
        return 'U'  # Unlock the door
    elif next_cell in ['*', 'T', '-'] and tools['d'] and not used_dynamite:  # Wall/tree/door and has unused dynamite
        return 'B'  # Blast the obstacle
    elif next_cell == '~' and tools['raft']:  # Water with raft
        return True
    elif next_cell in ['*', '~']:  # Wall or water without raft - don't move
        return False
    elif next_cell in ['T', '-']:  # Other obstacles without tools
        return False

    return True  # No obstacle, can move forward

# Update the tools map if the agent is on a cell with a tool
def update_tools(view, agent_local_pos):
    global tools, used_dynamite
    x, y = agent_local_pos
    cell_content = view[x][y]
    if cell_content == 'a':  # Axe
        tools['a'] = True
        print("Picked up axe!")
        # Update mental map to remove the axe
        global_pos = local_to_global((x, y), agent_global_pos)
        if 0 <= global_pos[0] < 20 and 0 <= global_pos[1] < 20:
            mental_map[global_pos[0]][global_pos[1]] = ' '
    elif cell_content == 'k':  # Key
        tools['k'] = True
        print("Picked up key!")
        # Update mental map to remove the key
        global_pos = local_to_global((x, y), agent_global_pos)
        if 0 <= global_pos[0] < 20 and 0 <= global_pos[1] < 20:
            mental_map[global_pos[0]][global_pos[1]] = ' '
    elif cell_content == 'd':  # Dynamite
        tools['d'] = True
        print("Picked up dynamite!")
        # Update mental map to remove the dynamite
        global_pos = local_to_global((x, y), agent_global_pos)
        if 0 <= global_pos[0] < 20 and 0 <= global_pos[1] < 20:
            mental_map[global_pos[0]][global_pos[1]] = ' '
    elif cell_content == '$':  # Treasure
        global has_treasure
        has_treasure = True
        print("Found treasure!")
        # Update mental map to remove the treasure
        global_pos = local_to_global((x, y), agent_global_pos)
        if 0 <= global_pos[0] < 20 and 0 <= global_pos[1] < 20:
            mental_map[global_pos[0]][global_pos[1]] = ' '

def handle_tool_use(action):
    global tools, used_dynamite
    if action == 'B':  # Using dynamite
        used_dynamite = True
        tools['d'] = False
    elif action == 'C':  # Using axe to chop tree
        tools['raft'] = True  # Get raft after chopping tree
    elif action == 'U':  # Using key to unlock door
        tools['k'] = False  # Key is used up

# Get the direction to face for the next step
def get_direction_to_face(current_direction, desired_direction):
    directions = ['^', '>', 'v', '<']
    current_idx = directions.index(current_direction)
    desired_idx = directions.index(desired_direction)
    turns_needed = (desired_idx - current_idx) % 4
    
    if turns_needed == 1:
        return 'R'
    elif turns_needed == 3:
        return 'L'
    elif turns_needed == 2:
        return 'R'  # Default to turning right if 180-degree turn is needed
    return 'F'  # No turn needed

def find_best_path(mental_map, start, targets, tools):
    # Consider tool usage in path cost
    # Add weights to different types of obstacles
    # Consider tool availability when planning paths
    pass

def prioritize_tools(mental_map, current_pos):
    # Analyze the map to determine which tools are most valuable
    # Return a priority order for tool collection
    pass

def explore_new_area(mental_map, current_pos, current_direction):
    # Try to find unexplored areas
    unexplored_directions = []
    x, y = current_pos
    
    # Check all four directions for unexplored areas
    if x > 0 and mental_map[x-1][y] == ' ':  # Up
        unexplored_directions.append('^')
    if x < len(mental_map)-1 and mental_map[x+1][y] == ' ':  # Down
        unexplored_directions.append('v')
    if y > 0 and mental_map[x][y-1] == ' ':  # Left
        unexplored_directions.append('<')
    if y < len(mental_map[0])-1 and mental_map[x][y+1] == ' ':  # Right
        unexplored_directions.append('>')
    
    if unexplored_directions:
        # Choose the direction that leads to the most unexplored area
        best_direction = unexplored_directions[0]
        max_unexplored = 0
        
        for direction in unexplored_directions:
            count = 0
            if direction == '^':
                for i in range(x-1, -1, -1):
                    if mental_map[i][y] == ' ':
                        count += 1
                    else:
                        break
            elif direction == 'v':
                for i in range(x+1, len(mental_map)):
                    if mental_map[i][y] == ' ':
                        count += 1
                    else:
                        break
            elif direction == '<':
                for j in range(y-1, -1, -1):
                    if mental_map[x][j] == ' ':
                        count += 1
                    else:
                        break
            elif direction == '>':
                for j in range(y+1, len(mental_map[0])):
                    if mental_map[x][j] == ' ':
                        count += 1
                    else:
                        break
            
            if count > max_unexplored:
                max_unexplored = count
                best_direction = direction
        
        # Convert direction symbol to command
        if best_direction != current_direction:
            # Calculate the number of clockwise turns needed
            directions = ['^', '>', 'v', '<']
            current_idx = directions.index(current_direction)
            desired_idx = directions.index(best_direction)
            turns_needed = (desired_idx - current_idx) % 4
            
            # Return the appropriate turn command
            if turns_needed == 1:
                return 'R'  # Turn clockwise
            elif turns_needed == 3:
                return 'L'  # Turn counter-clockwise
            else:
                return 'R'  # If it's 2 turns, either way works, default to R
        else:
            return 'F'  # If we're already facing the right direction, move forward
    
    return None

def find_alternative_path(mental_map, current_pos, target_pos):
    # Try to find a path around obstacles
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Up, Down, Left, Right
    visited = set()
    queue = [(current_pos, [])]
    
    while queue:
        (x, y), path = queue.pop(0)
        if (x, y) == target_pos:
            return path
        
        if (x, y) in visited:
            continue
        visited.add((x, y))
        
        for dx, dy in directions:
            new_x, new_y = x + dx, y + dy
            if (0 <= new_x < 20 and 0 <= new_y < 20 and 
                (new_x, new_y) not in visited and 
                mental_map[new_x][new_y] not in ['*', 'T', '-', '~']):
                new_path = path + [(new_x, new_y)]
                queue.append(((new_x, new_y), new_path))
    
    return None

def get_action(view):
    try:
        global agent_global_pos, start_pos, has_treasure
        agent_local_pos = get_agent_pos(view)
        if not agent_local_pos:
            return 'F'

        # Update agent's global position
        agent_global_pos = local_to_global(agent_local_pos, agent_global_pos)
        agent_direction = view[agent_local_pos[0]][agent_local_pos[1]]
        transformed_view = transform_view_based_on_orientation(view, agent_direction)
        update_mental_map(transformed_view, agent_global_pos, agent_direction)
        update_tools(transformed_view, agent_local_pos)

        if not start_pos:
            start_pos = agent_global_pos

        if not has_treasure:
            for i in range(5):
                for j in range(5):
                    if view[i][j] == '$':
                        has_treasure = True
                        break
                if has_treasure:
                    break

        if has_treasure:
            if agent_global_pos == start_pos:
                return 'F'
            path = dijkstra(mental_map, agent_global_pos, [start_pos])
            if not path:
                # If we can't find a path back to start, try to explore
                new_direction = explore_new_area(mental_map, agent_global_pos, view[agent_local_pos[0]][agent_local_pos[1]])
                if new_direction:
                    return new_direction
                return 'F'
            next_step = path[0]
        else:
            # First, look for unblocked paths to tools and treasure
            targets = []
            for i in range(20):
                for j in range(20):
                    if mental_map[i][j] in ['a', 'k', 'd', '$']:
                        # Try to find a path to the target
                        path = dijkstra(mental_map, agent_global_pos, [(i, j)])
                        if not path:
                            # If direct path is blocked, try to find an alternative path
                            alt_path = find_alternative_path(mental_map, agent_global_pos, (i, j))
                            if alt_path:
                                path = alt_path
                        if path:
                            targets.append((i, j))
            
            if targets:
                # Find the closest target
                closest_target = min(targets, key=lambda t: len(dijkstra(mental_map, agent_global_pos, [t])))
                path = dijkstra(mental_map, agent_global_pos, [closest_target])
                if path:
                    next_step = path[0]
                else:
                    # If we can't reach any targets, try to explore new areas
                    new_direction = explore_new_area(mental_map, agent_global_pos, view[agent_local_pos[0]][agent_local_pos[1]])
                    if new_direction:
                        return new_direction
                    
                    # If no new areas to explore, look for obstacles we can remove
                    if obstacles_to_remove:
                        path = dijkstra(mental_map, agent_global_pos, list(obstacles_to_remove))
                        if path:
                            next_step = path[0]
                        else:
                            obstacles_to_remove.clear()
                            if agent_path:
                                next_step = agent_path.pop()
                            else:
                                # If we're completely stuck, try to explore in a new direction
                                new_direction = explore_new_area(mental_map, agent_global_pos, view[agent_local_pos[0]][agent_local_pos[1]])
                                if new_direction:
                                    return new_direction
                                return 'F'
                    else:
                        # Look for new obstacles to remember
                        for i in range(20):
                            for j in range(20):
                                if mental_map[i][j] == 'T' and tools['a']:  # Tree with axe
                                    obstacles_to_remove.add((i, j))
                                elif mental_map[i][j] == '-' and tools['k']:  # Door with key
                                    obstacles_to_remove.add((i, j))
                                elif mental_map[i][j] == '*' and tools['d'] and not used_dynamite:  # Wall with unused dynamite
                                    obstacles_to_remove.add((i, j))
                        
                        if obstacles_to_remove:
                            path = dijkstra(mental_map, agent_global_pos, list(obstacles_to_remove))
                            if path:
                                next_step = path[0]
                            else:
                                obstacles_to_remove.clear()
                                if agent_path:
                                    next_step = agent_path.pop()
                                else:
                                    # If we're stuck, try to explore
                                    new_direction = explore_new_area(mental_map, agent_global_pos, view[agent_local_pos[0]][agent_local_pos[1]])
                                    if new_direction:
                                        return new_direction
                                    return 'F'
                        else:
                            # If no obstacles to remove, try to explore in a new direction
                            new_direction = explore_new_area(mental_map, agent_global_pos, view[agent_local_pos[0]][agent_local_pos[1]])
                            if new_direction:
                                return new_direction
                            # If no new areas to explore, try turning right
                            current_direction = view[agent_local_pos[0]][agent_local_pos[1]]
                            if current_direction == '^':
                                return 'R'
                            elif current_direction == 'v':
                                return 'L'
                            elif current_direction == '<':
                                return 'R'
                            elif current_direction == '>':
                                return 'L'
            else:
                # If no targets found, try to explore new areas
                new_direction = explore_new_area(mental_map, agent_global_pos, view[agent_local_pos[0]][agent_local_pos[1]])
                if new_direction:
                    return new_direction
                # If no new areas to explore, try turning right
                current_direction = view[agent_local_pos[0]][agent_local_pos[1]]
                if current_direction == '^':
                    return 'R'
                elif current_direction == 'v':
                    return 'L'
                elif current_direction == '<':
                    return 'R'
                elif current_direction == '>':
                    return 'L'

        next_step_local = global_to_local(next_step, agent_global_pos)
        action = can_move_forward(view, agent_local_pos)
        
        if action in ['C', 'U', 'B']:
            handle_tool_use(action)
            # Remove the obstacle from our set after using the tool
            if action == 'C':
                obstacles_to_remove = {(x, y) for x, y in obstacles_to_remove if mental_map[x][y] != 'T'}
            elif action == 'U':
                obstacles_to_remove = {(x, y) for x, y in obstacles_to_remove if mental_map[x][y] != '-'}
            elif action == 'B':
                obstacles_to_remove = {(x, y) for x, y in obstacles_to_remove if mental_map[x][y] != '*'}
            return action
        elif action == True:
            agent_path.append(agent_global_pos)
            return 'F'
        else:
            # If we can't move forward, try to find an alternative path
            if agent_path:
                next_step = agent_path.pop()
                return get_action(view)  # Recursively try to find a new path
            else:
                # If no path available, try to explore in a new direction
                new_direction = explore_new_area(mental_map, agent_global_pos, view[agent_local_pos[0]][agent_local_pos[1]])
                if new_direction:
                    return new_direction
                current_direction = view[agent_local_pos[0]][agent_local_pos[1]]
                if current_direction == '^':
                    return 'R'
                elif current_direction == 'v':
                    return 'L'
                elif current_direction == '<':
                    return 'R'
                elif current_direction == '>':
                    return 'L'
    except Exception as e:
        print(f"Error in get_action: {e}")
        return 'F'

# Helper function to print the grid
def print_grid(view):
    print('+-----+')
    for ln in view:
        print("|"+str(ln[0])+str(ln[1])+str(ln[2])+str(ln[3])+str(ln[4])+"|")
    print('+-----+')

def cleanup_agent_path():
    # Remove redundant path entries
    # Limit path length to prevent memory issues
    pass

def connect_with_timeout(host, port, timeout=5):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        return sock
    except socket.timeout:
        print("Connection timed out")
        sys.exit(1)

def validate_view(view):
    # Check for invalid characters
    # Validate view dimensions
    # Ensure agent position is valid
    pass

def print_mental_map():
    print("\nMental Map (20x20):")
    print("+" + "-" * 40 + "+")
    for row in mental_map:
        print("|", end="")
        for cell in row:
            print(f"{cell:2}", end="")
        print(" |")
    print("+" + "-" * 40 + "+")

if __name__ == "__main__":
    # Checks for correct amount of arguments 
    if len(sys.argv) != 3:
        print("Usage Python3 "+sys.argv[0]+" -p port \n")
        sys.exit(1)

    port = int(sys.argv[2])

    # Checking for valid port number
    if not 1025 <= port <= 65535:
        print('Incorrect port number')
        sys.exit()

    # Creates TCP socket
    sock = connect_with_timeout('localhost', port)

    # Navigates through grid with input stream of data
    i=0
    j=0
    while True:
        data=sock.recv(100)
        if not data:
            exit()
        for ch in data:
            if (i==2 and j==2):
                view[i][j] = '^'
                view[i][j+1] = chr(ch)
                j+=1 
            else:
                view[i][j] = chr(ch)
            j+=1
            if j>4:
                j=0
                i=(i+1)%5
        if j==0 and i==0:
            print("\nReceived new view:")
            print_grid(view)  # Print the current view
            
            # Get agent's position in the view
            agent_local_pos = get_agent_pos(view)
            if agent_local_pos:
                print(f"Agent position in view: {agent_local_pos}")
                print(f"Agent direction: {view[agent_local_pos[0]][agent_local_pos[1]]}")
            
            action = get_action(view)  # Gets new actions
            print(f"Selected action: {action}")
            print_mental_map()  # Print the mental map after each action
            sock.send(action.encode('utf-8'))

    sock.close()