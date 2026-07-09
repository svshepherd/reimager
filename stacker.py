import numpy as np
import os
from PIL import Image
import cv2
import colorcet as cc

def pic_stack(TARGET_FOLDER, COLORSHIFT=0, PALETTE='colorwheel'):
    '''
    COLORSHIFT = 0 for none, 1 for v1 or 2 for v2
    PALETTE = 'colorwheel' #'colorwheel'|'isolum'|'rainbow' 
    '''

    TARGET_FOLDER = os.path.abspath(TARGET_FOLDER)
    flist = [f for f in os.listdir(TARGET_FOLDER)]
    n_im = len(flist)

    im = 0*cv2.imread(os.path.join(TARGET_FOLDER,flist[0]),cv2.IMREAD_COLOR)
    if COLORSHIFT==1:
        hsv_part = 255*np.ones(im.shape).astype('uint8')
    im = im.astype('float64')

    for n,f in enumerate(flist):
        if not COLORSHIFT:
            img = cv2.imread(os.path.join(TARGET_FOLDER,f),cv2.IMREAD_COLOR).astype('float64')/255/n_im
            im += img
        else:
            img = cv2.imread(os.path.join(TARGET_FOLDER,f),cv2.IMREAD_GRAYSCALE).astype('float64')/255/n_im
            if COLORSHIFT==1:
                img = np.stack([img,img,img],axis=-1)
                hsv_part[:,:,0] = (255*n/n_im) # still uint8
                im += img*cv2.cvtColor(hsv_part.astype('uint8'), cv2.COLOR_HSV2BGR).astype('float64')/255
            elif COLORSHIFT==2:
                rgba_cmap = cc.cm[PALETTE](int(255*n/len(flist)))
                cmap = (rgba_cmap[2], rgba_cmap[1], rgba_cmap[0])
                im += np.stack([img*cmap[0],img*cmap[1],img*cmap[2]],axis=-1)
            else:
                raise
    if COLORSHIFT:
        lab = cv2.cvtColor((255*im).astype('uint8'), cv2.COLOR_BGR2LAB)
        lab[:,:,0] -= lab[:,:,0].min()
        lab[:,:,0] = ( lab[:,:,0].astype(float) * 255 / lab[:,:,0].max() ).round().astype(int)
        for layer in 1,2:
            lab_layer = lab[:,:,layer].astype('float')
            lab_layer -= lab_layer.mean()
            # for whatever reason this performed poorly:
            #lab_layer -= (lab_layer*lab[:,:,0]).sum()/lab[:,:,0].sum() 
            lab_layer = 127.5*lab_layer/abs(lab_layer).max()+127.5
            lab_layer = lab_layer.round().astype('uint8')
            lab[:,:,layer] = lab_layer
        img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        cv2.imwrite(f'mergedim.png',img)
    else:
        cv2.imwrite(f'mergedim.png',(255*im).astype('uint8'))


_SUPPORTED_EXTS = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp', '.webp'}


def align_images(TARGET_FOLDER, REFERENCE_IDX=0):
    """Compute ECC warp matrices to align all frames to a reference frame.

    Run this once and pass the result to ``pic_stack_isolum`` via ``warps=``
    to avoid redundant alignment computation across multiple stacking calls.

    Parameters
    ----------
    TARGET_FOLDER : str
        Folder containing input images.
    REFERENCE_IDX : int
        Index within the sorted file list to use as the alignment anchor.

    Returns
    -------
    flist : list[str]
        Sorted list of image filenames (basenames) within TARGET_FOLDER.
    warps : list[numpy.ndarray]
        2×3 float32 Euclidean warp matrix per frame; identity for the
        reference frame and any frame where ECC fails to converge.
    """
    TARGET_FOLDER = os.path.abspath(TARGET_FOLDER)
    flist = sorted(
        f for f in os.listdir(TARGET_FOLDER)
        if os.path.splitext(f)[1].lower() in _SUPPORTED_EXTS
    )
    n_im = len(flist)
    if n_im == 0:
        raise ValueError(f"No supported images found in {TARGET_FOLDER!r}")

    ref_bgr = cv2.imread(os.path.join(TARGET_FOLDER, flist[REFERENCE_IDX]), cv2.IMREAD_COLOR)
    ref_gray = cv2.cvtColor(ref_bgr, cv2.COLOR_BGR2GRAY).astype('float32') / 255.0
    ecc_criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 500, 1e-6)

    warps = []
    for n, f in enumerate(flist):
        if n == REFERENCE_IDX:
            warps.append(np.eye(2, 3, dtype='float32'))
            continue
        img_gray = cv2.cvtColor(
            cv2.imread(os.path.join(TARGET_FOLDER, f), cv2.IMREAD_COLOR),
            cv2.COLOR_BGR2GRAY,
        ).astype('float32') / 255.0
        warp = np.eye(2, 3, dtype='float32')
        try:
            _, warp = cv2.findTransformECC(ref_gray, img_gray, warp, cv2.MOTION_EUCLIDEAN, ecc_criteria)
        except cv2.error:
            pass  # leave as identity
        warps.append(warp)
    return flist, warps


def pic_stack_isolum(
    TARGET_FOLDER,
    PALETTE='CET_I1',
    REFERENCE_IDX=0,
    TINT_ALPHA=0.1,
    OUTPUT_PATH='mergedim_isolum.png',
    warps=None,
):
    """Align-and-stack with isoluminant percentile color tinting.

    Each aligned frame is blended as ``(1 - TINT_ALPHA) * natural_color +
    TINT_ALPHA * luminance * isoluminant_color``, where the isoluminant color
    comes from *PALETTE* at the frame's percentile position
    ``t = n / (N - 1)``.

    Parameters
    ----------
    TARGET_FOLDER : str
        Folder containing input images (jpg/png/tif/bmp/webp).
    PALETTE : str
        colorcet isoluminant colormap key, e.g. ``'CET_I1'``, ``'CET_I2'``,
        ``'CET_I3'``, ``'isolum'``, ``'cyclic_isoluminant'``.
    REFERENCE_IDX : int
        Index within the sorted file list to use as the alignment reference.
        Ignored when *warps* is supplied.
    TINT_ALPHA : float
        Blend weight for the isoluminant tint in [0, 1].
        ``0.0`` → pure natural color stack; ``1.0`` → fully tinted monochrome.
    OUTPUT_PATH : str or None
        Path to write the result PNG.  Pass ``None`` to skip writing.
    warps : list[numpy.ndarray] or None
        Pre-computed warp matrices from ``align_images()``.  When provided,
        ECC is skipped entirely.  The list must correspond to the same sorted
        file order that ``align_images`` returns.

    Returns
    -------
    numpy.ndarray
        Final stacked BGR image (uint8, HxWx3).
    """
    TARGET_FOLDER = os.path.abspath(TARGET_FOLDER)
    flist = sorted(
        f for f in os.listdir(TARGET_FOLDER)
        if os.path.splitext(f)[1].lower() in _SUPPORTED_EXTS
    )
    n_im = len(flist)
    if n_im == 0:
        raise ValueError(f"No supported images found in {TARGET_FOLDER!r}")
    if warps is not None and len(warps) != n_im:
        raise ValueError(f"len(warps)={len(warps)} does not match {n_im} images in folder")

    ref_bgr = cv2.imread(os.path.join(TARGET_FOLDER, flist[REFERENCE_IDX]), cv2.IMREAD_COLOR)
    h, w = ref_bgr.shape[:2]

    # Only needed when computing alignment internally
    if warps is None:
        ref_gray = cv2.cvtColor(ref_bgr, cv2.COLOR_BGR2GRAY).astype('float32') / 255.0
        ecc_criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 500, 1e-6)

    accum = np.zeros((h, w, 3), dtype='float64')

    for n, f in enumerate(flist):
        img_bgr = cv2.imread(os.path.join(TARGET_FOLDER, f), cv2.IMREAD_COLOR)

        # Resolve warp matrix
        if warps is not None:
            warp_mat = warps[n]
        elif n == REFERENCE_IDX:
            warp_mat = np.eye(2, 3, dtype='float32')
        else:
            img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY).astype('float32') / 255.0
            warp_mat = np.eye(2, 3, dtype='float32')
            try:
                _, warp_mat = cv2.findTransformECC(
                    ref_gray, img_gray, warp_mat, cv2.MOTION_EUCLIDEAN, ecc_criteria,
                )
            except cv2.error:
                pass

        # Apply warp (skip when it is exactly identity to avoid interpolation cost)
        if not np.allclose(warp_mat, np.eye(2, 3)):
            img_bgr = cv2.warpAffine(
                img_bgr, warp_mat, (w, h),
                flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP,
                borderMode=cv2.BORDER_REFLECT,
            )

        # Percentile position: frame n maps linearly across the full colormap
        t = n / max(n_im - 1, 1)
        rgba = cc.cm[PALETTE](t)          # (R, G, B, A) in [0, 1]
        c_r, c_g, c_b = rgba[0], rgba[1], rgba[2]

        lum = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY).astype('float64') / 255.0
        nat = img_bgr.astype('float64') / 255.0  # BGR planes

        # Blend: natural color + isoluminant tint
        accum[:, :, 0] += ((1 - TINT_ALPHA) * nat[:, :, 0] + TINT_ALPHA * lum * c_b) / n_im
        accum[:, :, 1] += ((1 - TINT_ALPHA) * nat[:, :, 1] + TINT_ALPHA * lum * c_g) / n_im
        accum[:, :, 2] += ((1 - TINT_ALPHA) * nat[:, :, 2] + TINT_ALPHA * lum * c_r) / n_im

    # LAB normalisation: always stretch L for contrast.
    # Zero-centre a/b only for full-tint mode (TINT_ALPHA==1); with natural color
    # blended in, forcing zero-mean chroma would desaturate the result.
    lab = cv2.cvtColor((255 * accum).astype('uint8'), cv2.COLOR_BGR2LAB)
    l_min, l_max = float(lab[:, :, 0].min()), float(lab[:, :, 0].max())
    if l_max > l_min:
        lab[:, :, 0] = (
            (lab[:, :, 0].astype('float64') - l_min) * 255 / (l_max - l_min)
        ).round().astype('uint8')
    if TINT_ALPHA >= 1.0:
        for ch in (1, 2):
            layer = lab[:, :, ch].astype('float64')
            layer -= layer.mean()
            peak = abs(layer).max()
            layer = (127.5 * layer / peak + 127.5) if peak > 0 else (layer + 127.5)
            lab[:, :, ch] = layer.round().clip(0, 255).astype('uint8')

    result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    if OUTPUT_PATH is not None:
        cv2.imwrite(OUTPUT_PATH, result)
    return result