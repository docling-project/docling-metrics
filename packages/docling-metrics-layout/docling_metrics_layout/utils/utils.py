def dict_get(data: dict, keys: list[str], default=None):
    r"""
    Traverse the given path of keys and return the value of dict
    If the path is broken return the default value
    """
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def xyxy_to_xywh(bbox: list[float]) -> list[float]:
    r"""
    The reverse of wywh_to_xyxy

    Assumptions:
    - Both input and output bbox is defined with the image origin at the top-left corner.
    - The input bbox is [x1, y1, x2, y2] where [x1, y1] is the top-left corner and [x2, y2] the
      bottom-right corner.
    - The output bbox is [x1, y1, width, height]
    """
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    xywh_bbox = [bbox[0], bbox[1], width, height]
    return xywh_bbox


def xywh_to_xyxy(bbox: list[float]) -> list[float]:
    r"""
    The reverse of xyxy_to_xywh

    Assumptions:
    - Both input and output bbox is defined with the image origin at the top-left corner.
    - The input bbox is [x1, y1, x2, y2] where [x1, y1] is the top-left corner and [x2, y2] the bottom-right corner.
    - The output bbox is [x1, y1, w, h]
    """
    xyxy_bbox = [
        bbox[0],
        bbox[1],
        bbox[0] + bbox[2],
        bbox[1] + bbox[3],
    ]
    return xyxy_bbox
