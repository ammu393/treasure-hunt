/*********************************************
 *  agent.c
 *  Sample Agent for Text-Based Adventure Game
 *  UNSW COMP3411/9814 Artificial Intelligence
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "pipe.h"

#define MAX_QUEUE_SIZE 1000
#define MAX_PATH_LENGTH 100

// Queue structure for BFS
typedef struct {
    int x, y;
    char path[MAX_PATH_LENGTH];
    int path_length;
} Node;

typedef struct {
    Node items[MAX_QUEUE_SIZE];
    int front;
    int rear;
    int size;
} Queue;

// Global variables
int pipe_fd;
FILE* in_stream;
FILE* out_stream;
char view[5][5];
static int have_axe = 0;
static int have_key = 0;
static int have_dynamite = 0;
static int have_raft = 0;
static int have_treasure = 0;

// Queue operations
void init_queue(Queue* q) {
    q->front = 0;
    q->rear = -1;
    q->size = 0;
}

int is_empty(Queue* q) {
    return q->size == 0;
}

void enqueue(Queue* q, Node node) {
    if (q->size < MAX_QUEUE_SIZE) {
        q->rear = (q->rear + 1) % MAX_QUEUE_SIZE;
        q->items[q->rear] = node;
        q->size++;
    }
}

Node dequeue(Queue* q) {
    Node node = q->items[q->front];
    q->front = (q->front + 1) % MAX_QUEUE_SIZE;
    q->size--;
    return node;
}

// Helper function to check if a position is safe to move to
static int is_safe(char c) {
    return c == ' ' || c == 'a' || c == 'k' || c == 'd' || c == '$';
}

// Helper function to check if we can use a tool on an obstacle
static int can_use_tool(char obstacle) {
    if (obstacle == 'T' && have_axe) return 1;
    if (obstacle == '-' && have_key) return 1;
    if ((obstacle == '*' || obstacle == 'T' || obstacle == '-') && have_dynamite) return 1;
    return 0;
}

// Helper function to check if a position is valid in the 5x5 view
static int is_valid_pos(int x, int y) {
    return x >= 0 && x < 5 && y >= 0 && y < 5;
}

// Helper function to get next action from path
static char get_next_action(const char* path) {
    if (path[0] == '\0') return 'R';  // Default action if no path
    return path[0];
}

// BFS to find path to goal
static char* find_path_to_goal(char view[5][5], int start_x, int start_y) {
    Queue q;
    init_queue(&q);
    
    // Create start node
    Node start = {start_x, start_y, "", 0};
    enqueue(&q, start);
    
    // Visited array to prevent cycles
    int visited[5][5] = {0};
    visited[start_x][start_y] = 1;
    
    // Current direction (0: up, 1: right, 2: down, 3: left)
    int current_dir = 0;  // Start facing up
    
    // Possible moves: up, right, down, left
    int dx[] = {-1, 0, 1, 0};
    int dy[] = {0, 1, 0, -1};
    
    while (!is_empty(&q)) {
        Node current = dequeue(&q);
        
        // Check if current position has a goal (tool or treasure)
        char current_char = view[current.x][current.y];
        if (current_char == 'a' || current_char == 'k' || 
            current_char == 'd' || current_char == '$') {
            return strdup(current.path);
        }
        
        // Try all possible moves
        for (int i = 0; i < 4; i++) {
            // Calculate new position based on current direction
            int new_x = current.x + dx[i];
            int new_y = current.y + dy[i];
            
            if (is_valid_pos(new_x, new_y) && !visited[new_x][new_y]) {
                char next_char = view[new_x][new_y];
                
                // Check if move is possible
                if (is_safe(next_char) || can_use_tool(next_char) || 
                    (next_char == '~' && have_raft)) {
                    
                    visited[new_x][new_y] = 1;
                    
                    // Create new path
                    Node next = {new_x, new_y, "", current.path_length + 1};
                    strcpy(next.path, current.path);
                    
                    // Calculate required direction changes and movement
                    int target_dir = i;
                    int dir_diff = (target_dir - current_dir + 4) % 4;
                    
                    // Add direction changes to path
                    if (dir_diff == 1) {
                        next.path[next.path_length++] = 'R';
                    } else if (dir_diff == 3) {
                        next.path[next.path_length++] = 'L';
                    }
                    
                    // Add forward movement
                    next.path[next.path_length++] = 'F';
                    
                    enqueue(&q, next);
                }
            }
        }
    }
    
    return NULL;  // No path found
}

char get_action(char view[5][5]) {
    // If we have treasure and are at start position, we've won
    if (have_treasure && view[2][2] == '^') {
        return 'F';
    }
    
    // Find path to nearest goal using BFS
    char* path = find_path_to_goal(view, 2, 2);  // Start from center (agent position)
    
    if (path != NULL) {
        char action = get_next_action(path);
        free(path);
        return action;
    }
    
    // If no path found, use simple obstacle avoidance
    char front = view[2][3];
    if (front == '*' || front == 'T' || front == '-' || (front == '~' && !have_raft)) {
        if (is_safe(view[2][3]) || can_use_tool(view[2][3])) return 'R';
        if (is_safe(view[2][1]) || can_use_tool(view[2][1])) return 'L';
        return 'R';
    }
    
    if (is_safe(front)) return 'F';
    return 'R';
}

void print_view()
{
  int i,j;

  printf("\n+-----+\n");
  for( i=0; i < 5; i++ ) {
    putchar('|');
    for( j=0; j < 5; j++ ) {
      if(( i == 2 )&&( j == 2 )) {
        putchar( '^' );
      }
      else {
        putchar( view[i][j] );
      }
    }
    printf("|\n");
  }
  printf("+-----+\n");
}

int main( int argc, char *argv[] )
{
  char action;
  int sd;
  int ch;
  int i,j;

  if ( argc < 3 ) {
    printf("Usage: %s -p port\n", argv[0] );
    exit(1);
  }

    // open socket to Game Engine
  sd = tcpopen("localhost", atoi( argv[2] ));

  pipe_fd    = sd;
  in_stream  = fdopen(sd,"r");
  out_stream = fdopen(sd,"w");

  while(1) {
      // scan 5-by-5 wintow around current location
    for( i=0; i < 5; i++ ) {
      for( j=0; j < 5; j++ ) {
        if( !(( i == 2 )&&( j == 2 ))) {
          ch = getc( in_stream );
          if( ch == -1 ) {
            exit(1);
          }
          view[i][j] = ch;
        }
      }
    }

    print_view(); // COMMENT THIS OUT BEFORE SUBMISSION
    action = get_action( view );
    putc( action, out_stream );
    fflush( out_stream );
  }

  return 0;
}
