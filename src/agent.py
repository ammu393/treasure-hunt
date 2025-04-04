#!/usr/bin/python3
# ^^ note the python directive on the first line
# COMP3411/9814 agent initiation file 
# requires the host to be running before the agent
# typical initiation would be (file in working directory, port = 31415)
#        python3 agent.py -p 31415
# created by Leo Hoare
# with slight modifications by Alan Blair


# The environment is represented as a dictionary (self.env) where keys are coordinates (x, y) and values are tile types (e.g., 'T' for trees, '-' for doors, '*' for walls, etc.).
# The agent maintains bounds (north_bounds, east_bounds, etc.) to track the explored area and dynamically updates the environment as it moves.
# A Pathfinding* Used to find the shortest path to a target (e.g., key, treasure). The heuristic is the Manhattan distance, which is admissible and ensures optimality.
# Handles obstacles like walls, trees, and doors by checking if the agent has the necessary tools (e.g., axe for trees, key for doors).
# Exploration is done through The agent explores unknown areas by expanding its view in all directions.It uses a breadth-first search (BFS) a
# pproach to prioritize nearby unexplored tiles.
# Som data structures used are:
# Priority Queue:Used in the A* algorithm to prioritize paths with the lowest estimated cost.Implemented using Python's heapq module.
# Sets:Used to store locations of objects like keys, axes, trees, and doors (self.axe, self.key, etc.).Ensures efficient lookup and avoids duplicates.
#Dictionary:The primary data structure for the environment (self.env), mapping coordinates to tile types.
#Allows efficient updates and lookups as the agent explores.

from enum import Enum
import sys
import socket
import heapq

# declaring visible grid to agent


class Compass:
    def __init__(self, start='n'):
        self.directions = ['n', 'e', 's', 'w']
        if start in self.directions:
            self.i = self.directions.index(start)
        else:
            self.i = 0  

    def left(self):
        self.i = (self.i - 1) % len(self.directions)

    def right(self):
        self.i = (self.i + 1) % len(self.directions)

    def curr(self):
        return self.directions[self.i]


class Agent:
    def __init__(self):
        self.env = {}  # dict mapping relative coordinates to tile types

        self.north_bounds = 0
        self.east_bounds = 0
        self.south_bounds = 0
        self.west_bounds = 0

        self.compass = Compass()

        self.axe = set()
        self.key = set()
        self.treasure = None
        self.trees = set()
        self.doors = set()
        self.dynamite = set()

        self.has_axe = False
        self.has_key = False
        self.has_treasure = False
        self.has_raft = False
        self.has_dynamite = False
        self.plan_ahead = False

        self.path = []
        self.moves = []

        self.x = 0
        self.y = 0

    def set_path(self, path):
        self.path = path
        self.moves = self.get_moves(path)
       # print(self.path)
        #print(self.moves)

    def clear_path(self):
        self.path = []
        self.moves = []

    def position_check(self):
        # create a poi list in priority order
        pois = []
        if not self.has_key:
            pois += list(self.key)
        if not self.has_axe:
            pois += list(self.axe)
        if not self.has_dynamite:
            pois += list(self.dynamite)
        pois = sorted(pois, key=lambda pos: abs(pos[0] - self.x) + abs(pos[1] - self.y))
        # go out of way to cut down doors
        if self.has_key:
            pois += sorted(self.doors, key=lambda pos: abs(pos[0] - self.x) + abs(pos[1] - self.y))

        # search for paths to each poi in priority order
        while pois:
            pos = pois.pop(0)
            print(pos)
            print('prev path')
            print(self.path)
            if self.path and pos == self.path[-1]:
                print('omg')
                # this poi was the previous target and there were no paths to pois of higher priority
                # check that the previous path is still valid
                valid = True
                for step in self.path:
                    if not self.valid(step):
                        valid = False
                        break
                if valid:
                    print('omg valid?')
                    return
                else:
                    self.clear_path()
            path = self.route(pos)
            print('path to axe')
            print(path)
            if path:
                print(path)
                self.set_path(path)
                return 
            
    def get_action(self):
        if self.has_treasure:
            if not self.moves:
                path = self.route((0,0))
                self.set_path(path)
            else:
                # check current path is still valid
                for step in self.path:
                    if not self.valid(step):
                        path = self.route((0,0))
                        self.set_path(path)
                        break
            return self.moves.pop(0)
        if self.treasure:
            self.check_treasure()

        if not self.moves or self.path[-1] != self.treasure:
            print('in here')
            self.position_check()

        if not self.moves:
            path = self.explore()
            if path:
                self.set_path(path)

            self.path.pop(0)

        
        return self.moves.pop(0)

    def check_treasure(self):
        if self.path and self.path[-1] == self.treasure:
            valid = True
            for move in self.path:
                if not self.valid(move):
                    valid = False
                    break
            if valid:
                return
            else:
                self.clear_path()
        path = self.route(self.treasure, False)
        if not path:
            path = self.route(self.treasure)
        if path:
            self.set_path(path)



    def expand_in_direction(self, a, b, direction, seen, queue):
        print(direction)
        if direction == 'N':
            x, y = a, b + 1
        elif direction == 'E':
            x, y = a + 1, b
        elif direction == 'S':
            x, y = a, b - 1
        elif direction == 'W':
            x, y = a - 1, b
        
        if (x, y) not in seen and self.valid((x, y)):
            print('valid for expansion')
            seen[(x, y)] = (a, b)
            if direction == 'N' or direction == 'S':
                range_check = range(x - 2, x + 3)
                for x1 in range_check:
                    if (x1, y + (2 if direction == 'N' else -2)) not in self.env or self.env[(x1, y + (2 if direction == 'N' else -2))] == '?':
                        step = (x, y)
                        path = [step]
                        while step != (self.x, self.y):
                            step = seen[step]
                            path.append(step)
                        path.reverse()
                        return path
            elif direction == 'E' or direction == 'W':
                range_check = range(y - 2, y + 3)
                for y1 in range_check:
                    if (x + (2 if direction == 'E' else -2), y1) not in self.env or self.env[(x + (2 if direction == 'E' else -2), y1)] == '?':
                        step = (x, y)
                        path = [step]
                        while step != (self.x, self.y):
                            step = seen[step]
                            path.append(step)
                            print("path from expansion")
                            print(path)
                        path.reverse()

                        return path
            queue.append((x, y))

        return None


    def explore(self):
        seen = {}
        queue = [(self.x, self.y)]
        while len(queue) > 0:
            pos = queue.pop(0)
            a, b = pos
            
            for direction in ['N', 'E', 'S', 'W']:
                result = self.expand_in_direction(a, b, direction, seen, queue)
                if result:
                    return result

        return [] 

    def get_moves(self, path):
        moves = []
        compass = Compass(self.compass.curr())
        
        for i, curr_tile in enumerate(path):
            if i + 1 >= len(path):
                break  # End of path
            
            next_tile = path[i + 1]
            direction_changes = self.get_direction_changes(compass, curr_tile, next_tile)
            
            if direction_changes is False:
                return False  # Bad path
            
            moves.extend(direction_changes)
            
            # Handle obstacles
            obstacle_moves = self.handle_obstacles(next_tile)
            moves.extend(obstacle_moves)
            
            # Append 'f' only if the agent can move forward
            if self.valid(next_tile):
                moves.append('f')
        
        return moves

    def get_direction_changes(self, compass, curr_tile, next_tile):
        x, y = curr_tile
        a, b = next_tile
        direction = compass.curr()
        moves = []
        
        if a == x and b == y + 1:
            # Go north
            if direction == 'e':
                compass.left()
                moves.append('l')
            elif direction == 's':
                compass.left()
                compass.left()
                moves.append('l')
                moves.append('l')
            elif direction == 'w':
                compass.right()
                moves.append('r')
        elif a == x + 1 and b == y:
            # Go east
            if direction == 's':
                compass.left()
                moves.append('l')
            elif direction == 'w':
                compass.left()
                compass.left()
                moves.append('l')
                moves.append('l')
            elif direction == 'n':
                compass.right()
                moves.append('r')
        elif a == x and b == y - 1:
            # Go south
            if direction == 'w':
                compass.left()
                moves.append('l')
            elif direction == 'n':
                compass.left()
                compass.left()
                moves.append('l')
                moves.append('l')
            elif direction == 'e':
                compass.right()
                moves.append('r')
        elif a == x - 1 and b == y:
            # Go west
            if direction == 'n':
                compass.left()
                moves.append('l')
            elif direction == 'e':
                compass.left()
                compass.left()
                moves.append('l')
                moves.append('l')
            elif direction == 's':
                compass.right()
                moves.append('r')
        else:
            # Bad path
            return False
        
        return moves

    def handle_obstacles(self, next_tile):
        moves = []
        
        if next_tile in self.env:
            tile = self.env[next_tile]
            if tile == '-' and self.has_key:
                moves.append('u') 
            elif tile == 'T' and self.has_axe:
                moves.append('c')  
            elif tile == '*' and self.has_dynamite:
                print('in here')
                if self.is_tool_accessible_after_blast(next_tile):
                    moves.append('b')  
                    print('appended b to moves')
                    moves.append('f')  
            elif tile == '*' or tile == '~':
                moves.append('l')
                moves.append('f')
        
        return moves


    def route(self, target, optimistic=True, start=None, env=None, has_axe=None, has_key=None, has_dynamite=None, has_raft=None):
        has_axe = has_axe or self.has_axe
        has_key = has_key or self.has_key
        has_dynamite = has_dynamite or self.has_dynamite
        has_raft = has_raft or self.has_raft
        seen = set([start])
        t_x, t_y = target
        start = (self.x, self.y)
        env = self.env
        # Priority queue: (estimated_cost, position, path)
        queue = [(0, start, [])]

        while len(queue) > 0:
            _, pos, path = heapq.heappop(queue)

            if pos == target:
                return [start] + path

            prev = len(path)
            curr_x, curr_y = pos
            expansions = [(curr_x, curr_y + 1), (curr_x + 1, curr_y), (curr_x, curr_y - 1), (curr_x - 1, curr_y)] 

            for exp in expansions:
                if exp not in seen:
                    tile = env.get(exp, '?')
                    if tile == 'T' and has_axe:
                        new_path = path + [exp]
                        heapq.heappush(queue, (prev + 5, exp, new_path))
                        seen.add(exp)
                    elif tile == '-' and has_key:
                        # Unlock the door and continue
                        new_path = path + [exp]
                        heapq.heappush(queue, (prev + 5, exp, new_path))  
                        seen.add(exp)
                    elif tile == '*' and has_dynamite:
                        if self.is_tool_accessible_after_blast(exp):
                                print('in heresss')
                                x,y = exp
                                print('next step')
                                print(self.env[x,y])
                                new_path = path + [exp]
                                print(new_path)
                                print('this is prev')
                                heapq.heappush(queue, (prev, exp, new_path))
                                print('this is the queue')
                                print(new_path) 
                                seen.add(exp)
                        has_dynamite = False

                    elif self.valid(exp, optimistic, env, has_axe, has_key, has_dynamite, has_raft):
                        dist = abs(exp[0] - t_x) + abs(exp[1] - t_y) + prev  
                        heapq.heappush(queue, (dist, exp, path + [exp]))
                        seen.add(exp)

        return []  # no path

    def valid(self, pos, optimistic=True, env=None, has_axe=None, has_key=None, has_dynamite=None, has_raft=None):
        env = env or self.env
        has_axe = has_axe or self.has_axe
        has_key = has_key or self.has_key
        has_dynamite = has_dynamite or self.has_dynamite
        has_raft = has_raft or self.has_raft
        if pos not in env:
            return False  
        tile = env[pos]
        if not optimistic and tile == '?':
            return False
        elif tile == 'T' and not has_axe:
            return False
        elif tile == '-' and not has_key:
            return False
        elif tile == '*':
            return False  
        elif tile == '~':
            return has_raft  
        else:
            return True

    def add_to_local_env(self, pos):
        if self.env[pos] == 'a' and pos not in self.axe:
            self.axe.add(pos)
        elif self.env[pos] == 'k' and pos not in self.key:
            self.key.add(pos)
        elif self.env[pos] == '$' and self.treasure != pos:
            self.treasure = pos
        elif self.env[pos] == 'd' and pos not in self.dynamite:
            self.dynamite.add(pos)
        elif self.env[pos] == 'T' and pos not in self.trees:
            self.trees.add(pos)
        elif self.env[pos] == '-' and pos not in self.doors:
            self.doors.add(pos)

    def on_object(self):
        pos = (self.x, self.y)
        curr = self.env[pos]
        if curr == 'a':
            self.axe.remove(pos)
            self.has_axe = True
        elif curr == 'k':
            self.key.remove(pos)
            self.has_key = True
        elif curr == 'd':
            self.dynamite.remove(pos)
            self.has_dynamite = True
        elif curr == '$':
            self.treasure = False
            self.has_treasure = True
        elif curr == 'T':
            self.trees.remove(pos)
            self.has_raft = True 

    def update_map(self, view, action):
        direction = self.compass.curr()
        
        if not self.env:  # First appearance
            self.initialize_environment(view)
        elif action == 'f':
            self.update_environment_on_move(view, direction)
        elif action in ['l', 'r']:
            self.update_compass(action)
        elif action in ['c', 'u', 'b']:
            self.update_environment_after_action(view, direction, action)
        
        # Additional logic for POI (Point of Interest) can be added here if needed
        if action == 'f':
            self.on_object()

    def initialize_environment(self, view):
        self.env = view
        self.env[(0, 0)] = ' '
        self.north_bounds = 2
        self.east_bounds = 2
        self.south_bounds = -2
        self.west_bounds = -2
        for y in range(2, -3, -1):
            for x in range(-2, 3):
                self.add_to_local_env((x, y))

    def update_environment_on_move(self, view, direction):
        if direction == 'n':
            self.update_north(view)
        elif direction == 'e':
            self.update_east(view)
        elif direction == 's':
            self.update_south(view)
        elif direction == 'w':
            self.update_west(view)

    def update_north(self, view):
        self.y += 1
        curr = self.env[(self.x, self.y)]
        if curr in ['*', 'T', '-']:
            self.y -= 1
            return 
        
        for x in range(-2, 3):
            self.env[(self.x + x, self.y + 2)] = view[(x, 2)]
            self.add_to_local_env((self.x + x, self.y + 2))
        
        self.env[(self.x, self.y - 1)] = view[(0, -1)]
        if self.y + 2 > self.north_bounds:
            self.north_bounds = self.y + 2
            self.update_border_north()

    def update_east(self, view):
        self.x += 1
        curr = self.env[(self.x, self.y)]
        if curr in ['*', 'T', '-']:
            self.x -= 1
            return  
        
        for x in range(-2, 3):
            self.env[(self.x + 2, self.y - x)] = view[(x, 2)]
            self.add_to_local_env((self.x + 2, self.y - x))
        
        self.env[(self.x - 1, self.y)] = view[(0, -1)]
        if self.x + 2 > self.east_bounds:
            self.east_bounds = self.x + 2
            self.update_border_east()

    def update_south(self, view):
        self.y -= 1
        curr = self.env[(self.x, self.y)]
        if curr in ['*', 'T', '-']:
            self.y += 1
            return  
        
        for x in range(-2, 3):
            self.env[(self.x - x, self.y - 2)] = view[(x, 2)]
            self.add_to_local_env((self.x - x, self.y - 2))
        
        self.env[(self.x, self.y + 1)] = view[(0, -1)]
        if self.y - 2 < self.south_bounds:
            self.south_bounds = self.y - 2
            self.update_border_south()

    def update_west(self, view):
        self.x -= 1
        curr = self.env[(self.x, self.y)]
        if curr in ['*', 'T', '-']:
            self.x += 1
            return  # nothing happens when you try and walk into wall, tree or door
        
        for x in range(-2, 3):
            self.env[(self.x - 2, self.y + x)] = view[(x, 2)]
            self.add_to_local_env((self.x - 2, self.y + x))
        
        self.env[(self.x + 1, self.y)] = view[(0, -1)]
        if self.x - 2 < self.west_bounds:
            self.west_bounds = self.x - 2
            self.update_border_west()

    def update_border_north(self):
        for x in range(self.west_bounds, self.east_bounds + 1):
            if (x, self.north_bounds) not in self.env:
                self.env[(x, self.north_bounds)] = '?'

    def update_border_east(self):
        for y in range(self.south_bounds, self.north_bounds + 1):
            if (self.east_bounds, y) not in self.env:
                self.env[(self.east_bounds, y)] = '?'

    def update_border_south(self):
        for x in range(self.west_bounds, self.east_bounds + 1):
            if (x, self.south_bounds) not in self.env:
                self.env[(x, self.south_bounds)] = '?'

    def update_border_west(self):
        for y in range(self.south_bounds, self.north_bounds + 1):
            if (self.west_bounds, y) not in self.env:
                self.env[(self.west_bounds, y)] = '?'

    def update_compass(self, action):
        if action == 'l':
            self.compass.left()
        elif action == 'r':
            self.compass.right()

    def update_environment_after_action(self, view, direction, action):
        x, y = self.get_front_tile(direction)
        self.env[(x, y)] = view[(0, 1)]
        
        self.trees.discard((x, y))
        self.doors.discard((x, y))
        if action == 'b':
            self.dynamite.discard((x, y))
            self.has_dynamite = False

    def get_front_tile(self, direction):
        if direction == 'n':
            return self.x, self.y + 1
        elif direction == 'e':
            return self.x + 1, self.y
        elif direction == 's':
            return self.x, self.y - 1
        elif direction == 'w':
            return self.x - 1, self.y
        
    def is_tool_accessible_after_blast(self, wall_tile):
        original_tile = self.env[wall_tile]
        self.env[wall_tile] = ' '

        accessible = False
        if self.axe and not accessible:
            for axe_pos in self.axe:
                path = self.route(axe_pos, optimistic=False)
                if path:
                    accessible = True
                    self.env[wall_tile] = original_tile
                    print(accessible)
                    return accessible

        if not accessible and self.treasure:
            path = self.route(self.treasure, optimistic=False, has_dynamite=False)
            #print('inside here')
           # print(path)
            if path:
                accessible = True
        self.env[wall_tile] = original_tile

        return accessible

    def show(self):
        print('show')
        print('axe: ' + str(self.axe))
        print('key: ' + str(self.key))
        print('treasure: ' + str(self.treasure))
        print('has_axe: ' + str(self.has_axe))
        print('has_key: ' + str(self.has_key))
        print('has_treasure: ' + str(self.has_treasure))
        print('trees: ' + str(self.trees))
        print('doors: ' + str(self.doors))
        print('has raft : ' + str(self.has_raft))
        print('has dynamites: ' + str(self.has_dynamite))


def print_view(view):
    print("+-----+")
    for y in range(2, -3, -1):
        line = '|'
        for x in range(-2, 3):
            if (x, y) == (0, 0): 
                line += '^'
            else:
                line += view.get((x, y), '?')  # Default to '?' if tile not in view
        line += '|'
        print(line)
    print("+-----+")

def connect_to_game_engine(host, port):
    try:
        sd = socket.create_connection((host, port))
        in_stream = sd.makefile('r')
        out_stream = sd.makefile('w')
        return in_stream, out_stream
    except Exception as e:
        print(f"Failed to connect to the game engine: {e}")
        sys.exit(1)

def read_view(in_stream):
    view = {}
    for y in range(2, -3, -1):
        for x in range(-2, 3):
            if (x, y) != (0, 0):  # Skip the agent's location
                ch = in_stream.read(1)
                if not ch:
                    print("Connection to the game engine lost.")
                    sys.exit(1)
                view[(x, y)] = ch
    return view

def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} -p <port>")
        sys.exit(1)

    in_stream, out_stream = connect_to_game_engine('localhost', int(sys.argv[2]))
    agent = Agent()
    action = ''

    # Main game loop
    while True:
        # Read the current view from the game engine
        view = read_view(in_stream)
        print_view(view)

        # Update the agent's map and decide the next action
        agent.update_map(view, action)
        agent.show()
        action = agent.get_action()

        # Send the action to the game engine
        out_stream.write(action)
        out_stream.flush()

if __name__ == "__main__":
    main()
