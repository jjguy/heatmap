#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <string.h>

float MIN_X = 0; 
float MIN_Y = 0;
float MAX_X = 0;
float MAX_Y = 0;

unsigned int WIDTH = 0;
unsigned int HEIGHT = 0;
int DOTSIZE = 0;

int DEBUG = 1;

struct point {
    float x;
    float y;
};

#ifdef WIN32
#define WIN32_LEAN_AND_MEAN
#include <Windows.h>

BOOL WINAPI DllMain(
    HINSTANCE hinstDLL,  // handle to DLL module
    DWORD fdwReason,     // reason for calling function
    LPVOID lpReserved )  // reserved
{
    // Perform actions based on the reason for calling.
    switch( fdwReason ) 
    { 
        case DLL_PROCESS_ATTACH:
            break;
        case DLL_THREAD_ATTACH:
            break;
        case DLL_THREAD_DETACH:
            break;
        case DLL_PROCESS_DETACH:
            break;
    }
    return TRUE;  // Successful DLL_PROCESS_ATTACH.
}
#endif

//walk the list of points, get the boundary values    
void getBounds(float *points, unsigned int cPoints)
{
    unsigned int i = 0;
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

    //and then map into our image dimentions
    pt.x = (int)(pt.x * WIDTH);
    pt.y = (int)((1-pt.y) * HEIGHT);

    return pt;
}

unsigned char* calcDensity(float *points, unsigned int cPoints)
{
    unsigned char* pixels = (unsigned char *)calloc(WIDTH*HEIGHT, sizeof(char)); 
    float midpt = DOTSIZE / 2;
    float radius = 0.5*sqrt(midpt*midpt + midpt*midpt);
    float dist = 0.0;
    int pixVal = 0;
    int j = 0;
    int k = 0;
    unsigned int i = 0;
    unsigned int ndx = 0;
    struct point pt; 

    // initialize image data to white
    for(i = 0; i < WIDTH*HEIGHT; i++) 
    {
        pixels[i] = 0xff;
    }

    for(i = 0; i < cPoints; i=i+2)
    {
        pt.x = points[i];
        pt.y = points[i+1];
        pt = translate(pt);

        for (j = pt.x - midpt; j < pt.x + midpt; j=j+1)
        {
            for (k = (pt.y-midpt); k < (pt.y+midpt); k=k+1)
            {
                if (j < 0 || k < 0 || j >= WIDTH || k >= HEIGHT) continue; 

                dist = sqrt( (j-pt.x)*(j-pt.x) + (k-pt.y)*(k-pt.y) );

                pixVal = (int)(200.0*(dist/radius)+50.0);
                if (pixVal > 255) pixVal = 255;

                ndx = j*WIDTH + k;
                if(ndx >= WIDTH*HEIGHT) continue;   // ndx can be greater than array bounds, despite constraints
                                                    // in for loop and if block
                pixels[ndx] = (pixels[ndx] * pixVal) / 255;
            } // for k
        } //for j
    } // for i

    return pixels;
}

unsigned char *colorize(unsigned char* pixels_bw, int *scheme, unsigned char* pixels_color, 
              unsigned int opacity)
{
    unsigned int i = 0;
    int pix = 0;

    for(i = 0; i < WIDTH*HEIGHT; i++)
    {
        pix = pixels_bw[i];
        pixels_color[i*4] = scheme[pix*3];
        pixels_color[i*4+1] = scheme[pix*3+1];
        pixels_color[i*4+2] = scheme[pix*3+2];
        pixels_color[i*4+3] = opacity;
    } 

    return pixels_color;
}

#ifdef WIN32
__declspec(dllexport)
#endif
unsigned char *tx(float *points, unsigned int cPoints, unsigned int w, unsigned int h, 
                  unsigned int dotsize, int *scheme, unsigned char *pix_color, unsigned int opacity)
{
    unsigned char *pixels_bw = NULL;

    //TODO - validate input

    DOTSIZE = dotsize;
    WIDTH = w;
    HEIGHT = h;
 
    // get min/max x/y values for point list
    getBounds(points, cPoints);

    //iterate through points, place a dot at each center point
    //and set pix value from 0 - 255 using multiply method for radius [dotsize]
    pixels_bw = calcDensity(points, cPoints);

    //using provided color scheme and opacity, update pixel value to RGBA values
    pix_color = colorize(pixels_bw, scheme, pix_color, opacity);

    free(pixels_bw);
    pixels_bw = NULL;

    //return list of RGBA values
    return pix_color;
}
