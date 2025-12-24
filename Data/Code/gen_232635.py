import pygame
import sys

# Initialize Pygame
pygame.init()

# Set up some constants
WIDTH, HEIGHT = 640, 480
BG_COLOR = (135, 206, 235)
FG_COLOR = (255, 255, 255)

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))

# Set up the font
font = pygame.font.Font(None, 36)

# Set up the clock
clock = pygame.time.Clock()

# Set up the bird
bird_x, bird_y = WIDTH / 2, HEIGHT / 2
bird_vx, bird_vy = 0, 0
bird_radius = 20
bird_color = (255, 0, 0)

# Set up the pipes
pipe_x, pipe_y = WIDTH, HEIGHT / 2
pipe_gap = 150
pipe_width = 80
pipe_color = (0, 255, 0)

# Set up the score
score = 0

# Game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # Make the bird jump
                bird_vy = -10

    # Move the bird
    bird_x += bird_vx
    bird_y += bird_vy
    bird_vy += 1  # gravity

    # Move the pipes
    pipe_x -= 5
    if pipe_x < -pipe_width:
        pipe_x = WIDTH
        score += 1

    # Check for collisions
    if (bird_x + bird_radius > pipe_x and
        bird_x - bird_radius < pipe_x + pipe_width and
        (bird_y - bird_radius < pipe_y - pipe_gap / 2 or
         bird_y + bird_radius > pipe_y + pipe_gap / 2)):
        # Game over
        print("Game Over! Final score:", score)
        pygame.quit()
        sys.exit()

    # Draw everything
    screen.fill(BG_COLOR)
    pygame.draw.circle(screen, bird_color, (int(bird_x), int(bird_y)), bird_radius)
    pygame.draw.rect(screen, pipe_color, (pipe_x, 0, pipe_width, pipe_y - pipe_gap / 2))
    pygame.draw.rect(screen, pipe_color, (pipe_x, pipe_y + pipe_gap / 2, pipe_width, HEIGHT - (pipe_y + pipe_gap / 2)))
    text = font.render(str(score), True, FG_COLOR)
    screen.blit(text, (WIDTH / 2, 20))

    # Update the display
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)

if __name__ == "__main__":
    pass