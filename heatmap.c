#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <string.h>

float MIN_X = 0;
float MIN_Y = 0;
float MAX_X = 0;
float MAX_Y = 0;

int WIDTH = 0;
int HEIGHT = 0;
int DOTSIZE = 0;

struct point {
    float x;
    float y;
};

#ifdef WIN32
#define WIN32_LEAN_AND_MEAN
#include <Windows.h>

BOOL WINAPI DllMain(    HINSTANCE hinstDLL,  // handle to DLL module
                        DWORD fdwReason,     // reason for calling function
                        LPVOID lpReserved )  // reserved
{
    return TRUE;
}
#endif

//walk the list of points, get the boundary values    
void getBounds(float *points, unsigned int cPoints)
{
    unsigned int i = 0;

    // first init the global counts
    MIN_X = points[i];
    MIN_Y = points[i+1];
    MAX_X = points[i];
    MAX_Y = points[i+1];

    //then iterate over the list and find the max/min values
    for(i = 0; i < cPoints; i=i+2)
    {
        float x = points[i];
        float y = points[i+1];

        if (x > MAX_X) MAX_X = x;
        if (x < MIN_X) MIN_X = x;

        if (y > MAX_Y) MAX_Y = y;
        if (y < MIN_Y) MIN_Y = y;
    }

    return;
}

//transform from dataset coordinates into image coordinates
struct point translate(struct point pt)
{
    // normalize the point into range 0..1
    pt.x = (pt.x - MIN_X) / (MAX_X - MIN_X);
    pt.y = (pt.y - MIN_Y) / (MAX_Y - MIN_Y);

    //and then map into our image dimentions.
    pt.x = (pt.x * WIDTH);
    pt.y = ((1-pt.y) * HEIGHT);

    return pt;
}

unsigned char* calcDensity(float *points, int cPoints)
{
    unsigned char* pixels = (unsigned char *)calloc(WIDTH*HEIGHT, sizeof(char)); 

    float midpt = DOTSIZE / 2.f;
    double radius = sqrt(midpt*midpt + midpt*midpt) / 2.f;
    double dist = 0.0;
    int pixVal = 0;
    int j = 0;
    int k = 0;
    int i = 0;
    int ndx = 0;
    struct point pt = {0};  

    // initialize image data to white
    for(i = 0; i < (int)WIDTH*HEIGHT; i++) 
    {
        pixels[i] = 0xff;
    }

    for(i = 0; i < cPoints; i=i+2)
    {
        pt.x = points[i];
        pt.y = points[i+1];
        pt = translate(pt);

        for (j = (int)pt.x - midpt; j < (int)pt.x + midpt; j++)
        {   
            for (k = (int)(pt.y - midpt); k < (int)(pt.y + midpt); k++)
            {
                if (j < 0 || k < 0 || j >= WIDTH || k >= HEIGHT) continue; 

                dist = sqrt( (j-pt.x)*(j-pt.x) + (k-pt.y)*(k-pt.y) );

                pixVal = (int)(200.0*(dist/radius)+50.0);
                if (pixVal > 255) pixVal = 255;

                ndx = k*WIDTH + j;
                if(ndx >= (int)WIDTH*HEIGHT) continue;   // ndx can be greater than array bounds

                #ifdef DEBUG
                printf("pt.x: %.2f pt.y: %.2f j: %d k: %d ndx: %d\n", pt.x, pt.y, j, k, ndx);
                #endif 

                pixels[ndx] = (pixels[ndx] * pixVal) / 255;
            } // for k
        } //for j
    } // for i

    return pixels;
}

unsigned char *colorize(unsigned char* pixels_bw, int *scheme, unsigned char* pixels_color, 
              int opacity)
{
    int i = 0;
    int pix = 0;
    int highCount = 0;
    int alpha = opacity;

    for(i = 0; i < (int)WIDTH*HEIGHT; i++)
    {
        pix = pixels_bw[i];

        if (pix < 0x10) highCount++;
        if (pix <= 252) 
            alpha = opacity; 
        else 
            alpha = 0;

        pixels_color[i*4] = scheme[pix*3];
        pixels_color[i*4+1] = scheme[pix*3+1];
        pixels_color[i*4+2] = scheme[pix*3+2];
        pixels_color[i*4+3] = alpha;
    } 
    
    if (highCount > WIDTH*HEIGHT*0.8)
    {   
        fprintf(stderr, "Warning: 80%% of output pixels are over 95%% density.\n");
        fprintf(stderr, "Decrease dotsize or increase output image resolution?\n");
    }

    return pixels_color;
}

#ifdef WIN32
__declspec(dllexport)
#endif
unsigned char *tx(float *points, 
                  int cPoints, 
                  int w, int h, 
                  int dotsize, 
                  int *scheme, 
                  unsigned char *pix_color, 
                  int opacity, 
                  int boundsOverride, 
                  float minX, float minY, float maxX, float maxY)
{
    unsigned char *pixels_bw = NULL;

    //basic sanity checks to keep from segfaulting
    if (NULL == points || NULL == scheme || NULL == pix_color ||
        w <= 0 || h <= 0 || cPoints <= 1 || opacity < 0 || dotsize <= 0)
    {
        fprintf(stderr, "Invalid parameter; aborting.\n");
        return NULL;
    }
        

    DOTSIZE = dotsize;
    WIDTH = w;
    HEIGHT = h;
 
    // get min/max x/y values from point list
    if (boundsOverride == 1)
    {
        MAX_X = maxX; MIN_X = minX;
        MAX_Y = maxY; MIN_Y = minY;
    }
    else
    {
        getBounds(points, cPoints);
    }

    #ifdef DEBUG
    printf("min: (%.2f, %.2f) max: (%.2f, %.2f)\n", MIN_X, MIN_Y, MAX_X, MAX_Y);
    #endif

    //iterate through points, place a dot at each center point
    //and set pix value from 0 - 255 using multiply method for radius [dotsize].
    pixels_bw = calcDensity(points, cPoints);

    //using provided color scheme and opacity, update pixel value to RGBA values
    pix_color = colorize(pixels_bw, scheme, pix_color, opacity);

    free(pixels_bw);
    pixels_bw = NULL;

    //return list of RGBA values
    return pix_color;
}
