# Purpose
This project is a Java library for performing MDS and inverse MDS calculations. 

# Building
There is an ANT script to build the JAR library. Simply run `ant` from the root directory to build the `test.jar` file, which can then be copied into the *Java* directory of the main Nebula project.

# Use
The JAR is executable and takes it's input over stdin as a JSON string. This JSON string is converted to a JSON object and then used to provide the MDS algorithms with its input data. The output is then returned over stdout as another JSON string.

## Input Format
```
{
    
    "highDimensions": int,
    "lowDimensions": int,
    "points": {
        pointId: {
            "highD": [],
            "lowD": []
        },
        ...
    },
    "weights": [],
    "inverse: boolean
}
```

* `highDimensions` is the number of dimensions in the high dimensional space. Required for both MDS and inverse MDS.
* `lowDimensions` is the number of dimensions in low dimensional space. For forward MDS, this is used as the target number of dimensions to reduce down to. For inverse MDS, this is simply used to help read the data. Default is 2 for forward MDS, required for inverse MDS.
* `points` is a map of points, each represented by a unique string ID, `pointId`, and each containing the following:
 * `highD` is an array representing the point's location in high dimensional space. Required for Both MDS and inverse MDS.
 * `lowD` is an array representing the point's location in low dimensional space. Required for inverse MDS. Ignored for forward MDS.
* `weights` is an array of weights to use for the MDS calculation. There should be one weight per dimension in the high dimensional space. Default is equal weights for each dimension for forward MDS. Ignored for inverse MDS.
* `inverse` indicates whether forward or inverse MDS should be performed. Default is false to indicate forward MDS.

## Output Format, Forward MDS
```
{
    "points": {
        pointId: {
            "pos": {
                "x": int,
                "y": int,
                "z": int
            }
        }
    }
}
```

A map of points is returned from forward MDS. Each point is identified by the same unique string ID, `pointId` provided to the algorithm. Within each point is a position object, which itself contains an x, y, and z value. This is hard coded into to work with 2 or 3 dimensions, and the z value is set to 0 when reduced down to 2 dimensions. It should be improved by making the position an array of arbitrary length.

## Output Format, Inverse MDS
```
{
    "weights": []
}
```

An array of weights is returned from inverse MDS, with each weight corresponding to a dimension in high dimensional space. I believe these weights should sum to 1.