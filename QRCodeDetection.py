
from matplotlib import pyplot
from matplotlib.patches import Rectangle 

from pyzbar.pyzbar import decode
from PIL import Image

import imageIO.png
import math



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

def scaleTo0And255AndQuantize(pixel_array, image_width, image_height):
    
    scale_array = createInitializedGreyscalePixelArray(image_width, image_height)
   t_value = computeMinAndMaxValues(pixel_array, image_width, image_height)
    
    if (t_value[0] == t_value[1]):
        return scale_array
    
    for i in range(image_height):
        for j in range(image_width):
            pixel = pixel_array[i][j]
            scale_array[i][j] = round((pixel - t_value[0]) * ((255 - 0) / (t_value[1] - t_value[0])) + 0)
    return scale_array 

def stretchContrast(pixel_array, image_width, image_height):
    min_value = 255
    max_value = 0

    for y in range(image_height):
        for x in range(image_width):
            if pixel_array[y][x] < min_value:
                min_value = pixel_array[y][x]
            if pixel_array[y][x] > max_value:
                max_value = pixel_array[y][x]

    return(min_value, max_value)

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

def edgeMagnitude(horizontal_edges, vertical_edges, image_width, image_height):
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

def computeDilation8Nbh3x3FlatSE(pixel_array, image_width, image_height):
    dilation = createInitializedGreyscalePixelArray(image_width, image_height)
    for i in range(image_width-1):
        for j in range(image_height-1):
            dilation[i][j] = 0
            
    for i in range(image_height):
        for j in range(image_width):
            if pixel_array[i][j] == pixel_array[0][j] and pixel_array[i][j] != 0:
                for x in range(0, 2):
                    for y in range(0, 2):
                        dilation[i + x][j + y] = 1
                        
            elif pixel_array[i][j] != 0:
                for x in range(-1, 2):
                    for y in range(-1, 2):
                        dilation[i + x][j + y] = 1
                
    
    return dilation 

def computeErosion8Nbh3x3FlatSE(pixel_array, image_width, image_height):
    erosion = createInitializedGreyscalePixelArray(image_width, image_height)
    for i in range(image_width-1):
        for j in range(image_height-1):
            erosion[i][j] = 0
    

    for i in range(1, image_height-1):
        for j in range(1, image_width-1):
            threeXthree_ones = True
            
            for x in range(-1, 2):
                for y in range(-1, 2):
                    if pixel_array[i + x][j + y] == 0:
                        threeXthree_ones = False
                        
            if threeXthree_ones:
                erosion[i][j] = 1 
            else:
                erosion[i][j] = 0
    
    return erosion 
class Queue:
    def __init__(self):
        self.items = []
    def isEmpty(self):
        return self.items == []
    def enqueue(self, item):
        self.items.insert(0,item)
    def dequeue(self):
        return self.items.pop()
    def size(self):
        return len(self.items)   
    
def computeConnectedComponentLabeling(pixel_array, image_width, image_height):
    connectedcomponent = createInitializedGreyscalePixelArray(image_width, image_height)
    visited = set()
    componentSizes= {}
    componentLabel = 1
    
    for i in range(image_height):
        for j in range(image_width):
            if (pixel_array[i][j] != 0) and ((i, j) not in visited):
                
                q = Queue()
                q.enqueue((i, j))
                visited.add((i,j))
                count = 0
                
                while q.size() != 0:
                    x, y = q.dequeue()
                    connectedcomponent[x][y] = componentLabel
                    
                   
                    if (x + 1 < image_height) and ((x + 1, y) not in visited) and (pixel_array[x + 1][y] != 0):
                        q.enqueue((x + 1, y))
                        visited.add((x + 1, y)) 
                        
                    if (0 <= x - 1) and ((x - 1, y) not in visited) and (pixel_array[x - 1][y] != 0):
                        q.enqueue((x - 1, y))
                        visited.add((x - 1, y))

                    if (0 <= y - 1) and ((x, y - 1) not in visited) and (pixel_array[x][y - 1] != 0):
                        q.enqueue((x, y - 1))
                        visited.add((x, y - 1)) 
                        
                    if (y + 1 < image_width) and ((x, y + 1) not in visited) and (pixel_array[x][y + 1] != 0):
                         q.enqueue((x, y + 1))
                         visited.add((x, y + 1))

                componentLabel += 1

    for i in range(1, componentLabel):
        for j in connectedcomponent:
            count += j.count(i)
        componentSizes[i] = count
        count = 0

    return connectedcomponent, componentSizes
    
def FindLargestConnectedComponent(c_image, c_sizes, image_width, image_height):
    largeconnectedComponent = createInitializedGreyscalePixelArray(image_width, image_height)

    large_component = 0
    sizes_component = 0
    for i in c_sizes.keys():
        if c_sizes[i] > sizes_component:
            sizes_component = c_sizes[i]
            large_component = i

    box_min_x = image_width
    box_min_y = image_height
    box_max_x = 0
    box_max_y = 0
    for i in range(image_height):
        for j in range(image_width):
            if c_image[i][j] == large_component:
                largeconnectedComponent[i][j] = 255 
                
                if i < box_min_y:
                    box_min_y = i
                
                if j < box_min_x:
                    box_min_x = j
  
                if i > box_max_y:
                    box_max_y = i

                if j > box_max_x:
                    box_max_x = j

                
            else:
                largeconnectedComponent[i][j] = 0
    
    box_size = [box_min_x, box_min_y, box_max_x - box_min_x, box_max_y - box_min_y]

    return largest_connected_component, box_size
    
def computeBiggestComponent(c_image, c_sizes, image_width, image_height):
    big_array = createInitializedGreyscalePixelArray(image_width, image_height)

    biggest_clabel = 0
    max_value = 0

    for i in c_sizes.keys():
        if c_sizes[i] > max_value:
            max_value = c_sizes[i]

    for j in c_sizes.keys():
        if max_value == c_sizes[j]:
            biggest_clabel = j

    for y in range(image_height):
        for x in range(image_width):
            if c_image[y][x] == biggest_clabel:
                big_array[y][x] = 255

    return big_array
    
def extractBoundingBox(pixel_array, image_width, image_height):
    min_x = image_height
    min_y = image_height
    max_x = 0
    max_y = 0
    found_y = False

    for y in range(image_height):
        for x in range(image_width):
            if pixel_array[y][x] > 0 and found_y == False:
                min_y = y
                found_y = True
            if pixel_array[y][x] > 0 and x < min_x:
                min_x = x
            if pixel_array[y][x] > 0 and x > max_x:
                max_x = x
            if pixel_array[y][x] > 0 and y > max_y:
                max_y = y

    return min_x, min_y, max_x, max_y

def main():
    filename = "./images/covid19QRCode/poster1small.png"

    # we read in the png file, and receive three pixel arrays for red, green and blue components, respectively
    # each pixel array contains 8 bit integer values between 0 and 255 encoding the color values
    (image_width, image_height, px_array_r, px_array_g, px_array_b) = readRGBImageToSeparatePixelArrays(filename)

    pyplot.imshow(prepareRGBImageForImshowFromIndividualArrays(px_array_r, px_array_g, px_array_b, image_width, image_height))


    greyscale_array = computeRGBToGreyscale(px_array_r, px_array_g, px_array_b, image_width, image_height)
    scale_array = scaleTo0And255AndQuantize(greyscale_array, image_width, image_height)

    horizontal_array = computeHorizontalEdgesSobelAbsolute(greyscale_array, image_width, image_height)

    vertical_array = computeVerticalEdgesSobelAbsolute(greysale_array, image_width, image_height)

    edge_magnitude_array = edgeMagnitude(vertical_array, horizontal_array, image_width, image_height)

    smooth_edges = edge
    for i in range(2):
        smooth_edges = computeBoxAveraging3x3(smooth_edges, image_width, image_height)
    smooth_edges = scaleTo0And255AndQuantize(smooth_edges, image_width, image_height)

    threshold_array = computeThresholdGE(smooth_edges, 70, image_width, image_height)

    dilation_array = computeDilation8Nbh3x3FlatSE(threshold_array, image_width, image_height)
    dilation_array = computeDilation8Nbh3x3FlatSE(dilation_array, image_width, image_height)
    erosion_array = computeErosion8Nbh3x3FlatSE(dilation_array, image_width, image_height)
    erosion_array = computeErosion8Nbh3x3FlatSE(erosion_array, image_width, image_height)
    morphological = erosion_array


    (c_image, c_sizes) = computeConnectedComponentLabeling(erosion_array, image_width, image_height)

    biggest_component = computeBiggestComponent(c_image, c_sizes, image_width, image_height)

    minX, minY, maxX, maxY = extractBoundingBox(biggest_component, image_width, image_height) 
    
    pyplot.imshow(prepareRGBImageForImshowFromIndividualArrays(px_array_r, px_array_g, px_array_b, image_width, image_height))

    #Testing

    #Step 1
    #pyplot.imshow(px_array, cmap="gray")

    #Step 2 - 4
    #pyplot.imshow(edge, cmap="gray")

    #Step 5
    #pyplot.imshow(smooth_edges, cmap="gray")

    #Step 6
    #pyplot.imshow(threshold_array, cmap="gray")

    #Step 7
    #pyplot.imshow(morphological, cmap="gray")

    #Step 8
    #pyplot.imshow(biggest_component, cmap="gray")
    

    # get access to the current pyplot figure
    axes = pyplot.gca()
    # create a 70x50 rectangle that starts at location 10,30, with a line width of 3
    #rect = Rectangle( (10, 30), 70, 50, linewidth=3, edgecolor='g', facecolor='none' )
    rect = Rectangle( (minX, minY), maxX - minX, maxY - minY, linewidth=2, edgecolor='g', facecolor='none' )

    # paint the rectangle over the current plot
    axes.add_patch(rect)

    # plot the current figure
    pyplot.show()



if __name__ == "__main__":
    main()
