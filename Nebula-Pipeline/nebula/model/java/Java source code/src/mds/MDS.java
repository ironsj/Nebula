package mds;

import java.util.Random;

import javax.json.Json;
import javax.json.JsonArray;
import javax.json.JsonArrayBuilder;
import javax.json.JsonBuilderFactory;
import javax.json.JsonObject;
import javax.json.JsonObjectBuilder;
import javax.json.JsonReader;
import javax.json.JsonWriter;

import mdsj.MDSJ;

public class MDS {

	static Random rand = new Random(1000);

	public static void main(String[] args) {
		boolean inverse = false;
		int highDimensions, lowDimensions = 2;
		double[][] highD;
		double[][] lowD;
		double[] weights;
		String[] ids;
		String[] type;
		String distanceFunc = "euclidean";

		JsonBuilderFactory factory = Json.createBuilderFactory(null);
		JsonObjectBuilder builder = factory.createObjectBuilder();

		// Read JSON object from standard in
		JsonReader jsonReader = Json.createReader(System.in);
		JsonObject object = jsonReader.readObject();

		// Check if we are doing forward or inverse MDS
		if (object.containsKey("inverse")) {
			inverse = object.getBoolean("inverse");
		}

		if (object.containsKey("distanceFunc")) {
			distanceFunc = object.getString("distanceFunc");
		}

		// The number of dimensions to use for the low D space
		if (object.containsKey("lowDimensions"))
			lowDimensions = object.getInt("lowDimensions");

		// The number of dimensions in high D
		highDimensions = object.getInt("highDimensions");

		JsonObject points = object.getJsonObject("points");
		int count = points.size();

		highD = new double[count][highDimensions];
		lowD = new double[count][lowDimensions];
		ids = new String[count];
		weights = new double[highDimensions];
		type = new String[count];

		// Read in the weights to use for each dimension. If no weights
		// are given, all dimensions are weighted equally.
		if (object.containsKey("weights")) {
			JsonArray values = object.getJsonArray("weights");
			for (int i = 0; i < values.size(); i++) {
				weights[i] = values.getJsonNumber(i).doubleValue();
			}
		} else {
			for (int i = 0; i < weights.length; i++) {
				weights[i] = 1.0 / weights.length;
			}
		}

		int index = 0;
		for (String key : points.keySet()) {
			ids[index] = key;

			JsonObject positions = points.getJsonObject(key);

			// Read in all high dimensional coordinates
			JsonArray highDPos = positions.getJsonArray("highD");
			for (int i = 0; i < highDPos.size(); i++) {
				highD[index][i] = highDPos.getJsonNumber(i).doubleValue();
			}

			// If we are doing inverse MDS, read in low dimensional coordinates and type (selected or sample)
			if (inverse) {
				JsonArray lowDPos = positions.getJsonArray("lowD");
				for (int i = 0; i < lowDPos.size(); i++) {
					lowD[index][i] = lowDPos.getJsonNumber(i).doubleValue();
				}
				
				type[index] = position.getJsonString("type").getString();
			}

			index++;
		}

		if (inverse) {
			double[] newWeights = invMds(highD, lowD, weights, distanceFunc, type);

			// Create a JSON object to write back to standard out
			JsonArrayBuilder arrayBuilder = factory.createArrayBuilder();
			for (int i = 0; i < newWeights.length; i++) {
				arrayBuilder.add(newWeights[i]);
			}
			builder.add("weights", arrayBuilder);
		} else {
			double[][] projection = mds(highD, weights, lowDimensions);

			// Scale each dimension to be between -1 and 1
			for (int i = 0; i < lowDimensions; i++) {
				double max = 0.0;
				for (int j = 0; j < projection.length; j++) {
					double absVal = Math.abs(projection[j][i]);
					if (absVal > max) {
						max = absVal;
					}
				}
				for (int j = 0; j < projection.length; j++) {
					projection[j][i] = projection[j][i] / max;
				}
			}

			// Create a JSON object to write back to standard out
			for (int i = 0; i < projection.length; i++) {
				JsonArrayBuilder arrayBuilder = factory.createArrayBuilder();
				for (int j = 0; j < projection[i].length; j++) {
					arrayBuilder.add(projection[i][j]);
				}
				builder.add(ids[i], arrayBuilder);
			}
		}

		JsonObject returnObject = builder.build();
		JsonWriter jsonWriter = Json.createWriter(System.out);
		jsonWriter.write(returnObject);
		jsonWriter.close();
		jsonReader.close();
	}

	public static double[][] mds(double[][] highD) {
		if (highD.length > 0) {
			int dimensions = highD[0].length;
			double[] weights = new double[dimensions];
			for (int i = 0; i < dimensions; i++) {
				weights[i] = 1.0 / dimensions;
			}
			return mds(highD, weights);
		}
		return null;
	}

	public static double[][] mds(double[][] highD, double[] weights) {
		return mds(highD, weights, 2);
	}

	public static double[][] mds(double[][] highD, double[] weights, int dimensions) {
		return mds(highD, weights, dimensions, "euclidean");
	}

	public static double[][] mds(double[][] highD, double[] weights, int dimensions, String distanceFunc) {
		highD = Util.zScore(highD);
		double[][] pdist = Util.pairwiseDist(highD, weights, distanceFunc);
		double[][] projection = MDSJ.classicalScaling(pdist, dimensions);
		projection = Util.transpose(projection);
		return projection;
	}

	public static double[] invMds(double[][] highD, double[][] lowD) {
		return invMds(highD, lowD, "euclidean");
	}

	public static double[] invMds(double[][] highD, double[][] lowD, String highDDistanceFunc) {
		int dimensions = highD[0].length;

		double[] weights = new double[dimensions];

		for (int i = 0; i < dimensions; i++) {
			weights[i] = 1.0 / dimensions;
		}

		return invMds(highD, lowD, weights, highDDistanceFunc, new String[] {});
	}

	public static double[] invMds(double[][] highD, double[][] lowD, double[] weights) {
		return invMds(highD, lowD, weights, "euclidean", new String[] {});
	}

	public static double[] invMds(double[][] highD, double[][] lowD, double[] weights, String highDDistanceFunc, String[] type) {
		// highDdata is the raw high-d data nrow by ncol matrix
		// lowDpdist is the user-provided low-d data nrow by norw matrix
		// weight is the starting point of search 1 by ncol vector

		int row = highD.length;
		int col = highD[0].length;
		int[] flag = new int[col];
		// MAX changes speed linearly (number of iterations)
		int MAX = 500;
		double[] dummyweight = new double[lowD[0].length];
		for (int i = 0; i < dummyweight.length; i++)
			dummyweight[i] = 1.0 / dummyweight.length;
//		for (int i = 0; i < dummyweight.length; i++)
//			dummyweight[i] = 1;
		double[][] lowDpdist = Util.pairwiseDist(lowD, dummyweight, "euclidean");

		// Scale the lowDpdist so it sums to 2, so each distance represents
		// some fraction of the total distances
		double lowDSum = 0;
		for (double dd[] : lowDpdist)
			for (double d : dd)
				lowDSum += d;

		lowDSum /= 2;
		for (int i = 0; i < lowDpdist.length; i++)
			for (int j = 0; j < lowDpdist[i].length; j++)
				lowDpdist[i][j] /= lowDSum;

		highD = Util.zScore(highD);

		double proposedMove = 0;
		double[] step = new double[col];
		double[] curWeight = new double[col];
		double[] newWeight = new double[col];

		// initialize the step width for each dimension
		for (int i = 0; i < col; i++) {
			step[i] = 2.0 / col;
		}

		System.arraycopy(weights, 0, curWeight, 0, col);

		double stressCur;
		double stressNew;

		stressCur = stress(highD, lowDpdist, curWeight, highDDistanceFunc, type);

		for (int iter = 1; iter <= MAX; iter++) {
			for (int dim = 0; dim < col; dim++) {

				System.arraycopy(curWeight, 0, newWeight, 0, col);

				// check if step need adjustment
				if (flag[dim] >= 10) {
					// 10 consecutive accepts increase the step width
					step[dim] = step[dim] * 2;
					flag[dim] = 0;
				} else if (flag[dim] <= -10) {
					// 10 consecutive reject decrease the step width
					step[dim] = step[dim] / 2;
					flag[dim] = 0;
				}

				newWeight[dim] = proposal(curWeight[dim], step[dim]);
				// call vectorscale to test order of operations
				newWeight = Util.scaleVector(newWeight);

				// stressCur = stress(highDdata, lowDpdist, movedFlag,
				// curWeight, movedPoint, movedPointNum);
				stressNew = stress(highD, lowDpdist, newWeight, highDDistanceFunc, type);

				if (stressNew < stressCur) {
					stressCur = stressNew;
					// accept the move
					System.arraycopy(newWeight, 0, curWeight, 0, col);
					// if (flag[dim] >= 0) {
					flag[dim] = flag[dim] + 1;
					// } else {
					// flag[dim] = 0;
					// }
				} else {
					// reject the move
					// if (flag[dim] <= 0) {
					flag[dim] = flag[dim] - 1;
					// } else {
					// flag[dim] = 0;
					// }
				}
			}
		}

		return curWeight;
	}

	private static double stress(double[][] highD, double[][] lowDpdist,
			// double[] movedFlag,
			double[] weight, String distanceFunc, String[] type) {
		// int[] movedPoint,
		// int movedPointNum) {
		// highDdata is the raw high-d dataset nrow by ncol matrix
		// lowDpdist is the low-d pairwise distance matrix nrow by norw matrix
		// movedFlag is the binary indicator for moved or not 1 by nrow vector
		// weight is the weight vector stresss be evaluated 1 by ncol vector
		// type indicate the type of points (selected or sample point)

		int rows = highD.length;
		double[][] highDpdist = new double[rows][rows];
		// double[][] scaleMat = new double[rows][rows];
		double highDSum = 0;

		double output = 0;
		for (int i = 0; i < highD.length; i++) {
			for (int j = i + 1; j < highD.length; j++) {
				highDpdist[i][j] = Util.dist(highD[i], highD[j], weight, distanceFunc);
				highDpdist[j][i] = highDpdist[i][j];
				// scaleMat[i][j] = movedFlag[i] * movedFlag[j];
				highDSum += highDpdist[i][j];
			}
		}

		// Now scale the highDpdist so it sums to 2
		// for selected points, calculate highD and lowD difference, then sum up
		// for sample points, sum up highD and lowD respectively, then calculate difference
		double sampleHigh = 0;
		double sampleLow = 0;
		boolean hasType = !(type.length == 0 || type[0] == null);
		
		for (int i = 0; i < highD.length; i++) {
			for (int j = i + 1; j < highD.length; j++) {
				highDpdist[i][j] /= highDSum;
				
				if (hasType && !type[i].equals(type[j])) continue; //do not calculate the pairwise distance between selected points and sample points
				else if (hasType && type[i].equals("sample")) {
					sampleHigh += highDpdist[i][j];
					sampleLow += lowDpdist[i][j];
				}
				else {
//					output += Math.abs((highDpdist[i][j] - lowDpdist[i][j]));
					output += Math.pow((highDpdist[i][j] - lowDpdist[i][j]), 2);
				}				
			}
		}
		
		output += Math.pow((sampleHigh - sampleLow), 2);

		return output;
	}

	private static double proposal(double current, double step) {
		// current is the current location
		// step is maximal range of random move
		double output = -1;
		while (output < 0 || output > 1) {
			output = current + (Math.random() - 0.5) * step;
			// output = current + (rand.nextDouble() - 0.5) * step;
		}
		return output;
	}
}
