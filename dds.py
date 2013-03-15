# DdsImageFile.py -- a PIL loader for (some) .DDS (DirectX8 texture) files
# See http://www.randomly.org/projects/misc/ for updates.

# Copyright (c) 2002, Oliver Jowett <oliver@randomly.org>
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# This is a PIL loader for the .dds DirectX file format
#
# The DDS file format is described (somewhat) at:
#  http://msdn.microsoft.com/library/default.asp?url=/library/en-us/dx8_vb/directx_vb/Graphics/ProgrammersGuide/Appendix/DDSFileFormat/ovwDDSFileFormat.asp
#
# The DTX1 texture format is described at:
#  http://oss.sgi.com/projects/ogl-sample/registry/EXT/texture_compression_s3tc.txt

import struct, string,png
from StringIO import StringIO

dxt1Decoder = None
    
# dwFlags constants
DDSD_CAPS = 1
DDSD_HEIGHT = 2
DDSD_WIDTH = 4
DDSD_PITCH = 8
DDSD_PIXELFORMAT = 0x1000
DDSD_MIPMAPCOUNT = 0x20000
DDSD_LINEARSIZE = 0x80000
DDSD_DEPTH = 0x800000

DDSD_EXPECTED = DDSD_CAPS+DDSD_HEIGHT+DDSD_WIDTH+DDSD_PIXELFORMAT

# ddpfPixelFormat.dwFlags constants
DDPF_ALPHAPIXELS = 1
DDPF_FOURCC = 4
DDPF_RGB = 0x40
    
# ddsCaps.dwCaps1 constants
DDSCAPS_COMPLEX = 8
DDSCAPS_TEXTURE = 0x1000
DDSCAPS_MIPMAP = 0x00400000
    
DDSCAPS_EXPECTED = DDSCAPS_TEXTURE
#import pdb
def decodeBC3alphablock(data):
    out = ['', '', '', '']  # row accumulators
    # Decode next 8-byte block.        
    a0, a1 ,bits1,bits2= struct.unpack('<BBHI', data)
    bits = bits1 | (bits2 << 16)

    if a0 > a1:
        lookup = [a0, a1, (6*a0 + 1*a1)/7, (5*a0+2*a1)/7, (4*a0+3*a1)/7, (3*a0+4*a1)/7, \
                (2*a0+5*a1)/7, (a0+6*a1)/7]
    else:
        lookup = [a0, a1, (4*a0 + 1*a1)/5, (3*a0+2*a1)/5, (2*a0+3*a1)/5, (1*a0+4*a1)/5, \
                0, 255]
    lookup = map(chr,lookup)

    # Decode this block into 4x4 pixels
    # Accumulate the results onto our 4 row accumulators
    for yo in xrange(4):
        for xo in xrange(4):
            op = (bits & (7 << 45)) >> 45
            bits <<= 3
            out[yo] += lookup[op]
    out = reversed(map(reversed,out))

            

    # All done.
    return tuple(out)

# Python-only DXT1 decoder; this is slow!
# Better to use _dxt1.decodeDXT1 if you can
# (it's used automatically if available by DdsImageFile)
def pythonDecodeDXT1(data):
    # input: one "row" of data (i.e. will produce 4*width pixels)
    blocks = len(data) / 8  # number of blocks in row
    out = ['', '', '', '']  # row accumulators
    #out = [[],[],[],[]]

    for xb in xrange(blocks):
        # Decode next 8-byte block.        
        c0, c1, bits = struct.unpack('<HHI', data[xb*8:xb*8+8])

        # color 0, packed 5-6-5
        b0 = (c0 & 0x1f) << 3
        g0 = ((c0 >> 5) & 0x3f) << 2
        r0 = ((c0 >> 11) & 0x1f) << 3
        
        # color 1, packed 5-6-5
        b1 = (c1 & 0x1f) << 3
        g1 = ((c1 >> 5) & 0x3f) << 2
        r1 = ((c1 >> 11) & 0x1f) << 3
        #import pdb

        # Decode this block into 4x4 pixels
        # Accumulate the results onto our 4 row accumulators
        for yo in xrange(4):
            for xo in xrange(4):
                # get next control op and generate a pixel
                
                control = bits & 3
                bits = bits >> 2
                #pdb.set_trace()
                if control == 0:
                    out[yo] += chr(r0) + chr(g0) + chr(b0)
                    #out[yo] += [(r0 << 11) + (g0 << 5) + b0]
                elif control == 1:
                    out[yo] += chr(r1) + chr(g1) + chr(b1)
                    #out[yo] += [(r1 << 11) + (g1 << 5) + b1]
                elif control == 2:                                
                    if c0 > c1:
                        out[yo] += chr((2 * r0 + r1 + 1) / 3) + chr((2 * g0 + g1 + 1) / 3) + chr((2 * b0 + b1 + 1) / 3)
                        #out[yo] += [(((2 * r0 + r1 + 1) / 3) << 11) + (((2 * g0 + g1 + 1) / 3) << 5) + ((2 * b0 + b1 + 1) / 3)]
                    else:
                        out[yo] += chr((r0 + r1) / 2) + chr((g0 + g1) / 2) + chr((b0 + b1) / 2)
                        #out[yo] += [(((r0 + r1) / 2) << 11) + (((g0 + g1) / 2) << 5) + ((b0 + b1) / 2)]
                elif control == 3:
                    if c0 > c1:
                        out[yo] += chr((2 * r1 + r0 + 1) / 3) + chr((2 * g1 + g0 + 1) / 3) + chr((2 * b1 + b0 + 1) / 3)
                        #out[yo] += [(((2 * r1 + r0 + 1) / 3) << 16) + (((2 * g1 + g0 + 1) / 3) << 8) + ((2 * b1 + b0 + 1) / 3)]
                    else:
                        out[yo] += '\0\0\0'
                        #out[yo] += [0]
                #if out[yo][-1] > 65535:
                    #pdb.set_trace()

    # All done.
    return tuple(out)
def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

class DdsImageFile():
    format = 'DDS'
    format_description = 'DirectX8 DDS texture file'

    def open(self,fp):
        self._loaded = 0
        self.fp = fp
        
        # Check header
        header = self.fp.read(128)
        if header[:4] != 'DDS ':
            raise SyntaxError, 'Not a DDS file'

        dwSize, dwFlags, dwHeight, dwWidth, dwPitchLinear, dwDepth, dwMipMapCount, ddpfPixelFormat, ddsCaps = struct.unpack('<IIIIIII 44x 32s 16s 4x', header[4:])
        self.size = dwWidth, dwHeight
        self.depth = dwDepth

        if dwSize != 124:
            raise SyntaxError, 'Expected dwSize == 124, got %d' % dwSize

        if (dwFlags & DDSD_EXPECTED) != DDSD_EXPECTED:
            raise SyntaxError, 'Unsupported image flags: %08x' % dwFlags
        
        pf_dwSize, pf_dwFlags, pf_dwFourCC, pf_dwRGBBitCount, pf_dwRBitMask, pf_dwGBitMask, pf_dwBBitMask, pf_dwRGBAlphaBitMask = struct.unpack('<II4sIIIII', ddpfPixelFormat)
        if pf_dwSize != 32:
            raise SyntaxError, 'Expected pf_dwSize == 32, got %d' % pf_dwSize

        caps_dwCaps1, caps_dwCaps2 = struct.unpack('<II 8x', ddsCaps)
        if (caps_dwCaps1 & DDSCAPS_EXPECTED) != DDSCAPS_EXPECTED:
            raise SyntaxError, 'Unsupported image caps: %08x' % caps_dwCaps1

        # check for DXT1
        if (pf_dwFlags & DDPF_FOURCC != 0):
            if pf_dwFourCC == 'DXT1':
                if (pf_dwFlags & DDPF_ALPHAPIXELS != 0):
                    raise SyntaxError, 'DXT1 with Alpha not supported' # yet
                else:
                    self.mode = 'RGB'
                    self.load = self._loadDXTOpaque
            elif pf_dwFourCC == 'DXT5':
                self.mode = 'RGBA'
                self.load = self._loadDXT5
                #self.load = self._loadDXTOpaque
            else:
                raise SyntaxError, 'Unsupported FOURCC mode: %s' % pf_dwFourCC
        else:
            # XXX is this right? I don't have an uncompressed dds to play with
            self.mode = 'RGB'
            # Construct the tile.
            self.tile = [('raw', (0,0,dwWidth,dwHeight), 128,
                          ('RGBX', dwPitchLinear - dwWidth, 1))]

    def _loadDXT5(self):
        global dxt1Decoder
        
        if self._loaded: return
        if not dxt1Decoder:
        	# dxt1Decoder = pythonDecodeDXT1
            # Haven't selected a decoder yet. Try to get the C implementation
            try:
                import _dxt1
                dxt1Decoder = _dxt1.decodeDXT1
            except ImportError:
                #print "WARNING: Failed to import _dxt1 module."
                #print "WARNING: I'll use the slow python-based decoder instead."
                dxt1Decoder = pythonDecodeDXT1

        # one entry per Y row, we join them up at the end
        data = []
        #self.fp.seek(128) # skip header

        linesize = (self.size[0] + 3) / 4 * 16 # Number of data byte per row
        #import pdb

        baseoffset = 0
        #pdb.set_trace()
        for yb in xrange((self.size[1] + 3) / 4):             
            decoded = ['']*4
            for _ in xrange(linesize/16):             
                linealpha = decodeBC3alphablock(self.fp.read(8))
                pixels = dxt1Decoder(self.fp.read(8)) # returns 4-tuple of RGB lines

                for z in xrange(len(pixels)):
                    decoded[z] += ''.join([''.join(list(x)) for x in zip(chunks(pixels[z],3),linealpha[z])])
            for d in decoded:
                # Make sure that if we have a texture size that's not a
                # multiple of 4 that we correctly truncate the returned data
                data.append(d[:self.size[0]*4])
                #data.append(d)

        # Now build the final image from our data strings
        self.data = string.join(data[:self.size[1]],'')
        #self.data = data
        #self.im = Image.core.new(self.mode, self.size)
        #self.fromstring(data)
        self._loaded = 1

    def _loadDXTOpaque(self):
        global dxt1Decoder
        
        if self._loaded: return

        if not dxt1Decoder:
        	# dxt1Decoder = pythonDecodeDXT1
            # Haven't selected a decoder yet. Try to get the C implementation
            try:
                import _dxt1
                dxt1Decoder = _dxt1.decodeDXT1
            except ImportError:
                #print "WARNING: Failed to import _dxt1 module."
                #print "WARNING: I'll use the slow python-based decoder instead."
                dxt1Decoder = pythonDecodeDXT1

        # one entry per Y row, we join them up at the end
        data = []
        #self.fp.seek(128) # skip header

        linesize = (self.size[0] + 3) / 4 * 8 # Number of data byte per row
        #import pdb

        baseoffset = 0
        #pdb.set_trace()
        for yb in xrange((self.size[1] + 3) / 4):             
            linedata = self.fp.read(linesize)
            decoded = dxt1Decoder(linedata) # returns 4-tuple of RGB lines
            #data.extend(decoded)
            for d in decoded:
                # Make sure that if we have a texture size that's not a
                # multiple of 4 that we correctly truncate the returned data
                data.append(d[:self.size[0]*3])
                #data.append(d)

        # Now build the final image from our data strings
        self.data = string.join(data[:self.size[1]],'')
        #self.data = data
        #self.im = Image.core.new(self.mode, self.size)
        #self.fromstring(data)
        self._loaded = 1

def dds2png(f):
    dds = DdsImageFile()
    dds.open(f)
    dds.load()
    width,height = dds.size
    #print width,height
    #print len(dds.data)
    #for y in xrange(height-1,-1,-1):
        #for x in xrange(width):
            #print x,y,dds.data[3 * (y* width + x) : 3 * (y * width + x) + 3],'asdfasdf'
            #print len(dds.data[3 * (y* width + x) : 3 * (y * width + x) + 3])
    #raw_pixels = [[len(dds.data[3 * (y * width + x) : 3 * (y * width + x) + 3]) for x in xrange(width)] for y in xrange(height-1, -1, -1)]
    #print raw_pixels
    if dds.mode == 'RGB':
        raw_pixels = [[struct.unpack('BBB', dds.data[3 * (y * width + x) : 3 * (y * width + x) + 3]) for x in xrange(width)] for y in xrange(height-1, -1, -1)]
        pixels = [[c for px in row for c in (px[0], px[1], px[2], 255)] for row in raw_pixels]
    elif dds.mode == 'RGBA':
        raw_pixels = [[struct.unpack('BBBB', dds.data[4 * (y * width + x) : 4 * (y * width + x) + 4]) for x in xrange(width)] for y in xrange(height-1, -1, -1)]
        pixels = [[c for px in row for c in (px[0], px[1], px[2], px[3])] for row in raw_pixels]
    out = StringIO()
    w = png.Writer(width,height,alpha=True,compression=9)
    w.write(out, pixels)
    return out.getvalue()
