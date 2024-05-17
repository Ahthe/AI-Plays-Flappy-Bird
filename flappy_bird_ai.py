import pygame
import neat
import time
import os
import random
pygame.font.init()

WIN_WIDTH = 500
WIN_HEIGHT = 800


BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

STAT_FONT = pygame.font.SysFont("comicsans", 50)


class Bird:
    # Declaring the constants for the bird class
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    # how much we can rotate the bird on each frame
    ROT_VEL = 20
    # for how long we are going to show each bird
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        """
        Initiates the bird's jump by setting its velocity to a negative value,
        resetting the tick count, and updating the height from which the jump starts.
        Parameters:
        None
        Returns:
        None
        """
        self.vel = -10.5  # Sets the bird's velocity to -10.5 to move it upwards on the screen
        self.tick_count = 0  # Resets the tick count to 0 at the start of the jump
        self.height = self.y  # Updates the height from which the jump starts

    def move(self):
        """
        Updates the bird's position based on its current velocity and the time passed since the last move.
        This method also adjusts the bird's tilt based on its movement direction. The bird tilts upwards
        when moving up and tilts downwards when falling. The tilt is capped at a maximum rotation for upward
        movement and at -90 degrees for downward movement.

        Parameters:
        None

        Returns:
        None
        """
        self.tick_count += 1  # Increment the time since the last move

        # Calculate displacement
        d = self.vel * self.tick_count + 1.5 * self.tick_count ** 2  # Displacement formula

        if d >= 16:  # If displacement is greater than 16, cap it at 16
            d = 16

        if d < 0:  # If displacement is negative, make the jump more pronounced
            d -= 2

        self.y = self.y + d  # Update the bird's y position based on the displacement

        # Tilt the bird
        if d < 0 or self.y < self.height + 50:  # If moving upwards or not too far down, tilt the bird upwards
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:  # If moving downwards, tilt the bird downwards
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        """
        Draws the bird image on the window based on the bird's current animation frame.
        This method cycles through the bird images to simulate flapping. The cycle
        goes through all the bird images to create an animation effect, then resets.

        Parameters:
        win (pygame.Surface): The window or surface on which the bird image is drawn.

        Returns:
        None
        """
        self.img_count += 1  # Increment the image counter to move to the next frame

        # Determine which bird image to display based on the current frame
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]  # First bird image
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]  # Second bird image
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]  # Third bird image
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]  # Second bird image again for smooth transition
        elif self.img_count == self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]  # Reset to first bird image
            self.img_count = 0  # Reset image counter for next cycle

        # If the bird is tilting downwards significantly, switch to the second bird image
        # to simulate a nosedive.
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2

        # Rotate the bird image based on its current tilt
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        # Get the new rect for the rotated image, keeping the bird centered
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        # Draw the rotated image to the window
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)

class Pipe:
    GAP = 200
    VEL = 5
    WIDTH = PIPE_IMG.get_width()
    def __init__(self, x):
        self.x = x
        self.height = 0

        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        """
        Checks for a collision between the bird and either the top or bottom pipe.
        This is done by creating masks for the bird and the pipes, then checking
        if there's any overlap between the bird's mask and the pipe masks at their
        respective offsets.

        Parameters:
        bird (Bird): The Bird object to check for collision with the pipes.

        Returns:
        bool: True if there is a collision between the bird and any of the pipes,
        False otherwise.
        """
        bird_mask = bird.get_mask()  # Create a mask for the bird based on its current image
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)  # Create a mask for the top pipe
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)  # Create a mask for the bottom pipe

        # Calculate the offset between the bird and the top pipe, and between the bird and the bottom pipe
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        # Check for collisions between the bird mask and the top/bottom pipe masks at the calculated offsets
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        # Return True if a collision is detected with either the top or bottom pipe, False otherwise
        if b_point or t_point:
            return True

        return False

class Base:
    VEL = 5  # The velocity at which the base moves
    WIDTH = BASE_IMG.get_width()  # The width of the base image
    IMG = BASE_IMG  # The base image

    def __init__(self, y):
        """
        Initializes the Base object with a specified y-coordinate. It sets up two x-coordinates
        for the base images to create a continuous moving effect by cycling between these images.

        Parameters:
        y (int): The y-coordinate of the base's position.

        Returns:
        None
        """
        self.y = y  # The y-coordinate of the base
        self.x1 = 0  # The x-coordinate for the first base image
        self.x2 = self.WIDTH  # The x-coordinate for the second base image to create a seamless loop

    def move(self):
        """
        Moves the base to the left by decreasing the x-coordinates (x1 and x2) based on the velocity.
        It checks if either of the base images has moved completely out of the window and resets its
        position to create a continuous scrolling effect.

        Parameters:
        None

        Returns:
        None
        """
        self.x1 -= self.VEL  # Move the first base image to the left
        self.x2 -= self.VEL  # Move the second base image to the left

        # If the first base image is completely out of the window, reset its position to the right of the second image
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        # If the second base image is completely out of the window, reset its position to the right of the first image
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))  # Draw the first base image
        win.blit(self.IMG, (self.x2, self.y))  # Draw the second base image

def draw_window(win, bird, pipes, base, score):
    win.blit(BG_IMG, (0, 0))

    for pipe in pipes:
        pipe.draw(win)

    text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

    base.draw(win)
    bird.draw(win)
    pygame.display.update()

def main():
    """
    The main function initializes the game, creating a bird instance and the game window.
    It enters a loop that keeps the game running until the user decides to quit.
    Inside the loop, it processes events (like the user closing the window), moves the bird,
    and updates the display with the new game state.

    Parameters:
    None

    Returns:
    None
    """
    bird = Bird(230, 350)  # Create a Bird instance at position
    base = Base(730)  # Create a Base instance at position
    pipes = [Pipe(700)]  # Create a list of Pipe instances with a starting position
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))  # Initialize the game window with minimum dimensions
    clock = pygame.time.Clock()  # Create a clock object to keep track of the game

    score = 0

    run = True  # Game loop control variable
    while run:  # Game loop starts
        clock.tick(30)  # Limit the game loop to 30 frames per second
        for event in pygame.event.get():  # Event handling loop
            if event.type == pygame.QUIT:  # Check for QUIT event to stop the game
                run = False


        add_pipe = False # Variable to check if a new pipe needs to be added to the list
        rem = []
        for pipe in pipes:
            if pipe.collide(bird):  # Check for a collision between the bird and the pipe
                pass

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:  # Check if the pipe has moved out of the window
                rem.append(pipe)  # Remove the pipe from the list

            if not pipe.passed and pipe.x < bird.x:  # Check if the bird
                pipe.passed = True
                add_pipe = True

            pipe.move()

        if add_pipe:
            score += 1
            pipes.append(Pipe(700)) # Add a new pipe to the list

        for r in rem:
            pipes.remove(r)

        if bird.y + bird.img.get_height() >= 730: # Check if the bird is out of bounds
            pass

        # bird.move()  # Update the bird's position
        base.move()  # Update the base's position
        draw_window(win, bird, pipes, base, score)  # Redraw the game window with the updated bird position

    pygame.quit()  # Quit pygame after exiting the game loop
    quit()  # Quit the program

main()