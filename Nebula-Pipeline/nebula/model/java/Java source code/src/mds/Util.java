package mds;

public class Util {
	
	public static double cosineDist(double[] highD1, double[] highD2, double[] weights) {
        double numerator = 0;
        double denomonator1 = 0;
        double denomonator2 = 0;
        for (int i = 0; i < highD1.length; i++) {
            numerator += highD1[i] * highD2[i] * Math.pow(weights[i], 2);
            denomonator1 += Math.pow(highD1[i] * weights[i], 2);
            denomonator2 += Math.pow(highD2[i] * weights[i], 2);
        }
        denomonator1 = Math.pow(denomonator1, 0.5);
        denomonator2 = Math.pow(denomonator2, 0.5);
        return 1 - numerator / (denomonator1 * denomonator2);
    }
	 
	public static double euclideanDist(double[] highD1, double[] highD2, double[] weights) {
		double dist = 0;
		int cols = highD1.length;
		for (int i = 0; i < cols; i++) {
			dist = dist + Math.pow(highD1[i] - highD2[i], 2) * weights[i];
		}
		dist = Math.pow(dist, 0.5);
		return dist;
	}
	
	public static double dist(double[] highD1, double[] highD2, double[] weights, String distanceFunc) {
		if (distanceFunc.equals("cosine")) {
			return cosineDist(highD1, highD2, weights);
		} else {
			return euclideanDist(highD1, highD2, weights);
		}
	}
	

	public static double[][] pairwiseDist(double[][] highDData, double[] weights) {
		return pairwiseDist(highDData, weights, "cosine");
	}
	
	public static double[][] pairwiseDist(double[][] highDData, double[] weights, String distanceFunc) {
		int rows = highDData.length;

		double[][] output = new double[rows][rows];

		for (int i = 0; i < rows; i++) {
			for (int j = i + 1; j < rows; j++) {
					output[i][j] = dist(highDData[i], highDData[j], weights, distanceFunc);
					output[j][i] = output[i][j];
			}
		}
		return output;
	}
	
	
	public static double[][] transpose(double[][] input) {

		int rows = input.length;
		int cols = input[0].length;

		double[][] output = new double[cols][rows];

		for (int i = 0; i < rows; i++) {
			for (int j = 0; j < cols; j++) {
				output[j][i] = input[i][j];
			}
		}

		return output;
	}
	
	// pick one column of input matrix, col is the column index
    public static double[] pickCol(double[][] input, int col) {
        int row = input.length;
        double[] output = new double[row];
        for (int i = 0; i <= row - 1; i++) {
            output[i] = input[i][col];
        }
        return output;
    }

	// scale input vector by its sum (make it sum up to 1)
	public static double[] scaleVector(double[] input) {
		int col = input.length;
		double sum = 0;
		for (int i = 0; i < col; i++) {
			sum = sum + input[i];
		}

		double[] output = new double[col];
		for (int i = 0; i < col; i++) {
			output[i] = input[i] / sum;
		}
		return output;
	}

	// normalized input vector by its mean and variance
	public static double[] normalizeVector(double[] input) {
		int col = input.length;

		double n = col;

		double sum = 0;
		double ssx = 0;

		double mean = 0;
		double sd = 0;

		for (int i = 0; i < col; i++) {
			sum = sum + input[i];
		}
		mean = sum / n;

		for (int i = 0; i < col; i++) {
			ssx = ssx + Math.pow((input[i] - mean), 2);
		}

		sd = Math.pow(ssx / (n - 1), 0.5);

		for (int i = 0; i < col; i++) {
			if (sd == 0)
				input[i] = input[i] - mean;
			else
				input[i] = (input[i] - mean) / sd;
		}
		return input;
	}

	public static double[][] zScore(double[][] input) {

		int row = input.length;
		int col = input[0].length;
		double[] temp = new double[col];

		for (int i = 0; i <= col - 1; i++) {

			temp = pickCol(input, i);
			temp = normalizeVector(temp);
			for (int j = 0; j <= row - 1; j++) {
				input[j][i] = temp[j];
			}
		}
		return input;
	}
}
