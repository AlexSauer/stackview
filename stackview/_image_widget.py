from ipycanvas import Canvas
import numpy as np
from functools import lru_cache

class ImageWidget(Canvas):
    def __init__(self, image, zoom_factor:float=1.0, zoom_spline_order:int=0):
        if not ((len(image.shape) == 2) or (len(image.shape) == 3 and image.shape[-1] == 3)):
            raise NotImplementedError("Only 2D images are supported" + str(image.shape))
        height = image.shape[0] * zoom_factor
        width = image.shape[1] * zoom_factor
        self.zoom_factor = zoom_factor
        self.zoom_spline_order = zoom_spline_order
        super().__init__(width=width * zoom_factor, height=height * zoom_factor)
        self.data = np.asarray(image)
        self.layout.stretch = False

    @property
    def data(self):
        """Image data as numpy array
        """
        return self._data

    @data.setter
    def data(self, new_data):
        """Take in new image data, compress to PNG, send to image widget.
        """
        if new_data is None:
            return

        self._data = np.asarray(new_data)
        self._update_image()
        self.height = self._data.shape[0] * self.zoom_factor
        self.width = self._data.shape[1] * self.zoom_factor

    def _update_image(self):
        if self.zoom_factor == 1.0:
            self.put_image_data(_img_to_rgb(self._data), 0, 0)
        else:
            zoomed = self._zoom(self._data)
            self.put_image_data(_img_to_rgb(zoomed), 0, 0)

    def _zoom(self, data):
        if len(data.shape) == 3:
            # handle RGB images
            return np.asarray([self._zoom(data[:,:,i]) for i in range(data.shape[2])]).swapaxes(0, 2).swapaxes(1, 0)

        from scipy.ndimage import affine_transform
        matrix = np.asarray([[1.0 / self.zoom_factor, 0, -0.5],
                             [0, 1.0 / self.zoom_factor, -0.5],
                             [0, 0, 1],
                             ])
        zoomed_shape = (np.asarray(data.shape) * self.zoom_factor).astype(int)
        zoomed = affine_transform(data,
                                  matrix,
                                  output_shape=zoomed_shape,
                                  order=self.zoom_spline_order,
                                  mode='nearest')
        return zoomed


def _is_label_image(image):
    return image.dtype == np.uint32 or image.dtype == np.uint64 or \
           image.dtype == np.int32 or image.dtype == np.int64


def _img_to_rgb(image,
                display_min=None,
                display_max=None):

    if len(image.shape) == 3 and image.shape[2] == 3:
        return image

    if image.dtype == bool:
        image = image * 1

    if _is_label_image(image):
        lut = _labels_lut()
        return np.asarray([lut[:, c].take(image) for c in range(0, 3)]).swapaxes(0, 2).swapaxes(1, 0) * 255

    if display_min is None:
        display_min = image.min()
    if display_max is None:
        display_max = image.max()

    img_range = (display_max - display_min)
    if img_range == 0:
        img_range = 1

    image = (image - display_min) / img_range * 255
    return np.asarray([image, image, image]).swapaxes(0, 2).swapaxes(1, 0)

@lru_cache(maxsize=1)
def _labels_lut():
    from numpy.random import MT19937
    from numpy.random import RandomState, SeedSequence
    rs = RandomState(MT19937(SeedSequence(3)))
    lut = rs.rand(65537, 3)
    lut[0, :] = 0
    # these are the first four colours from matplotlib's default
    lut[1] = [0.12156862745098039, 0.4666666666666667, 0.7058823529411765]
    lut[2] = [1.0, 0.4980392156862745, 0.054901960784313725]
    lut[3] = [0.17254901960784313, 0.6274509803921569, 0.17254901960784313]
    lut[4] = [0.8392156862745098, 0.15294117647058825, 0.1568627450980392]
    return lut
