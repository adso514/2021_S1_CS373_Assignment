
from matplotlib import pyplot
from matplotlib.patches import Rectangle

import imageIO.png


def createInitializedGreyscalePixelArray(image_width, image_height, initValue = 0):

    new_array = [[initValue for x in range(image_width)] for y in range(image_height)]
    return new_array


# this function reads an RGB color png file and returns width, height, as well as pixel arrays for r,g,b
def readRGBImageToSeparatePixelArrays(input_filename):

    image_reader = imageIO.png.Reader(filename=input_filename)
    # png reader gives us width and height, as well as RGB data in image_rows (a list of rows of RGB triplets)
    (image_width, image_height, rgb_image_rows, rgb_image_info) = image_reader.read()

    print("read image width={}, height={}".format(image_width, image_height))

    # our pixel arrays are lists of lists, where each inner list stores one row of greyscale pixels
    pixel_array_r = []
    pixel_array_g = []
    pixel_array_b = []

    for row in rgb_image_rows:
        pixel_row_r = []
        pixel_row_g = []
        pixel_row_b = []
        r = 0
        g = 0
        b = 0
        for elem in range(len(row)):
            # RGB triplets are stored consecutively in image_rows
            if elem % 3 == 0:
                r = row[elem]
            elif elem % 3 == 1:
                g = row[elem]
            else:
                b = row[elem]
                pixel_row_r.append(r)
                pixel_row_g.append(g)
                pixel_row_b.append(b)

        pixel_array_r.append(pixel_row_r)
        pixel_array_g.append(pixel_row_g)
        pixel_array_b.append(pixel_row_b)

    return (image_width, image_height, pixel_array_r, pixel_array_g, pixel_array_b)

# This method packs together three individual pixel arrays for r, g and b values into a single array that is fit for
# use in matplotlib's imshow method
def prepareRGBImageForImshowFromIndividualArrays(r,g,b,w,h):
    rgbImage = []
    for y in range(h):
        row = []
        for x in range(w):
            triple = []
            triple.append(r[y][x])
            triple.append(g[y][x])
            triple.append(b[y][x])
            row.append(triple)
        rgbImage.append(row)
    return rgbImage
    

# This method takes a greyscale pixel array and writes it into a png file
def writeGreyscalePixelArraytoPNG(output_filename, pixel_array, image_width, image_height):
    # now write the pixel array as a greyscale png
    file = open(output_filename, 'wb')  # binary mode is important
    writer = imageIO.png.Writer(image_width, image_height, greyscale=True)
    writer.write(file, pixel_array)
    file.close() 
    
def computeRGBToGreyscale(pixel_array_r, pixel_array_g, pixel_array_b, image_width, image_height):
    greyscale_pixel_array = createInitializedGreyscalePixelArray(image_width, image_height)
    
    for i in range(image_height):
        
        for j in range(image_width):
            
            grey = 0.299 * pixel_array_r[i][j] + 0.587 * pixel_array_g[i][j] + 0.114 * pixel_array_b[i][j]
            
            greyscale_pixel_array[i][j] = round(grey)
    return greyscale_pixel_array 

def computeVerticalEdgesSobelAbsolute(pixel_array, image_width, image_height):
    greyscale_pixel_array = createInitializedGreyscalePixelArray(image_width, image_height)
    filter_kernels = {
        (-1, 1): -0.125, (0, 1): 0, (1, 1): 0.125,
        (-1, 0): -0.25, (0, 0): 0, (1, 0): 0.25,
        (-1, -1): -0.125, (0, -1): 0, (1, -1): 0.125
    }
    
    for i in range(1, image_height - 1):
        for j in range(1, image_width - 1):
            pixel = 0
            for x, y in filter_kernels:
                pixel += pixel_array[i + y][j + x] * filter_kernels[(x, y)]
                greyscale_pixel_array[i][j] = abs(pixel)
    return greyscale_pixel_array 

def computeHorizontalEdgesSobelAbsolute(pixel_array, image_width, image_height):
    greyscale_pixel_array = createInitializedGreyscalePixelArray(image_width, image_height)
    filter_kernels = {
        (-1, 1): 0.125, (0, 1): 0.25, (1, 1): 0.125,
        (-1, 0): 0, (0, 0): 0, (1, 0): 0,
        (-1, -1): -0.125, (0, -1): -0.25, (1, -1): -0.125
    }
    
    for i in range(1, image_height - 1):
        for j in range(1, image_width - 1):
            pixel = 0
            for x, y in filter_kernels:
                pixel += pixel_array[i + y][j + x] * filter_kernels[(x, y)]
                greyscale_pixel_array[i][j] = abs(pixel)
    return greyscale_pixel_array

def computeEdgeMagnitude(horizontal_edges, vertical_edges, image_width, image_height):
    magnitude_edges = []

    for height in range(image_height):
        row = []
        for width in range(image_width):
            magnitude_gradient = ((vertical_edges[height][width]**2) + (horizontal_edges[height][width])**2) ** 0.5
            row.append(magnitude_gradient)
        magnitude_edges.append(row)

    return magnitude_edges 

def computeBoxAveraging3x3(pixel_array, image_width, image_height):
    greyscale_edges = []
    
    for x in range(image_height):
        row = []
        for y in range(image_width):
            sum = 0
            if x == 0 or y == 0 or x == image_height - 1 or y == image_width - 1:
                row.append(0) 
            else: 
                a = (pixel_array[y - 1][x - 1]) + (pixel_array[y - 1][x]) + (pixel_array[y - 1][x + 1])
                b = (pixel_array[y][x - 1]) + (pixel_array[y][x]) + (pixel_array[y][x + 1])
                c = (pixel_array[y + 1][x - 1]) + (pixel_array[y + 1][x]) + (pixel_array[y + 1][x + 1])
                row.append((a + b + c) / 9)
        greyscale_edges.append(row)
    return greyscale_edges
             

def computeThresholdGE(pixel_array, threshold_value, image_width, image_height):
    threshold_array = []
    
    for i in range(image_height): 
        row = []
        for j in range(image_width):
            if pixel_array[i][j] >= threshold_value:
                row.append(255)
            else:
                row.append(0) 
        threshold_array.append(row)
    return threshold_array

def main():
    filename = "./images/covid19QRCode/poster1small.png"

    # we read in the png file, and receive three pixel arrays for red, green and blue components, respectively
    # each pixel array contains 8 bit integer values between 0 and 255 encoding the color values
    (image_width, image_height, px_array_r, px_array_g, px_array_b) = readRGBImageToSeparatePixelArrays(filename)

    pyplot.imshow(prepareRGBImageForImshowFromIndividualArrays(px_array_r, px_array_g, px_array_b, image_width, image_height))

    # get access to the current pyplot figure
    axes = pyplot.gca()
    # create a 70x50 rectangle that starts at location 10,30, with a line width of 3
    rect = Rectangle( (10, 30), 70, 50, linewidth=3, edgecolor='g', facecolor='none' )
    # paint the rectangle over the current plot
    axes.add_patch(rect)

    # plot the current figure
    pyplot.show()



if __name__ == "__main__":
    main()
