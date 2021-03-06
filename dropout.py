"""Dropout variants for multithreaded deep network training"""

import lasagne
import theano.tensor as T

class DropoutLayer(lasagne.layers.DropoutLayer):
    """Dropout layer which may have overlaps between worker threads"""

    def __init__(self, incoming, mask=None, **kwargs):
        super(DropoutLayer, self).__init__(incoming, **kwargs)
        self.mask = mask

    def get_output_for(self, linput, deterministic=False, **kwargs):
        if deterministic or self.p == 0:
            return linput
        else:
            # Using theano constant to prevent upcasting
            one = T.constant(1)

            retain_prob = one - self.p
            if self.rescale:
                linput /= retain_prob

            if self.mask:
                return linput * self.mask

            # use nonsymbolic shape for dropout mask if possible
            mask_shape = self.input_shape
            if any(s is None for s in mask_shape):
                mask_shape = linput.shape

            # apply dropout, respecting shared axes
            if self.shared_axes:
                shared_axes = tuple(a if a >= 0 else a + linput.ndim
                                    for a in self.shared_axes)
                mask_shape = tuple(1 if a in shared_axes else s
                                   for a, s in enumerate(mask_shape))
            mask = self._srng.binomial(mask_shape, p=retain_prob,
                                       dtype=linput.dtype)
            if self.shared_axes:
                bcast = tuple(bool(s == 1) for s in mask_shape)
                mask = T.patternbroadcast(mask, bcast)
            return linput * mask
