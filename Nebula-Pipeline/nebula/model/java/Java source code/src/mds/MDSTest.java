package mds;

import static org.junit.Assert.fail;

import java.util.Arrays;
import java.util.Comparator;
import java.util.Random;

import org.junit.Ignore;
import org.junit.Test;

public class MDSTest {

	// double[][] highD = new double[][] { { 1, 2, 3, 4, 5 }, { 0, 0, 20, 3, 1
	// }, { 2.3, 4.1, 2.3, 4.2, 5.2 } };
	// double[][] lowD = new double[][] { { 2, 3 }, { 0, 3 }, { 0, 0.5 } };
	double[][] highD = new double[][] { { 95.0, 14.0, 12.0, 2.0, 5.0 }, { 85.0, 6.0, 8.0, 7.0, 12.0 },
			{ 89.0, 19.0, 5.0, 10.0, 10.0 }, { 93.0, 8.0, 11.0, 9.0, 13.0 }, { 83.0, 7.0, 6.0, 0.0, 12.0 },
			{ 91.0, 17.0, 0.0, 6.0, 17.0 }, { 83.0, 15.0, 18.0, 10.0, 13.0 }, { 81.0, 11.0, 11.0, 0.0, 9.0 },
			{ 80.0, 18.0, 12.0, 18.0, 8.0 }, { 95.0, 19.0, 6.0, 13.0, 15.0 }, { 9.0, 88.0, 14.0, 0.0, 13.0 },
			{ 11.0, 87.0, 15.0, 7.0, 7.0 }, { 16.0, 91.0, 14.0, 12.0, 14.0 }, { 11.0, 90.0, 13.0, 13.0, 8.0 },
			{ 18.0, 80.0, 15.0, 9.0, 4.0 }, { 13.0, 90.0, 12.0, 9.0, 16.0 }, { 9.0, 98.0, 4.0, 11.0, 13.0 },
			{ 2.0, 91.0, 14.0, 3.0, 10.0 }, { 13.0, 91.0, 11.0, 7.0, 8.0 }, { 9.0, 95.0, 17.0, 19.0, 13.0 },
			{ 1.0, 4.0, 93.0, 3.0, 12.0 }, { 5.0, 5.0, 87.0, 18.0, 0.0 }, { 9.0, 13.0, 88.0, 15.0, 9.0 },
			{ 8.0, 7.0, 84.0, 8.0, 19.0 }, { 18.0, 1.0, 90.0, 12.0, 5.0 }, { 13.0, 19.0, 91.0, 9.0, 2.0 },
			{ 9.0, 3.0, 91.0, 14.0, 9.0 }, { 16.0, 19.0, 83.0, 7.0, 5.0 }, { 13.0, 1.0, 95.0, 0.0, 18.0 },
			{ 14.0, 16.0, 81.0, 5.0, 8.0 }, { 4.0, 0.0, 10.0, 95.0, 15.0 }, { 7.0, 13.0, 5.0, 97.0, 0.0 },
			{ 12.0, 16.0, 19.0, 88.0, 2.0 }, { 4.0, 14.0, 9.0, 80.0, 11.0 }, { 3.0, 2.0, 2.0, 81.0, 6.0 },
			{ 9.0, 15.0, 16.0, 82.0, 18.0 }, { 15.0, 1.0, 3.0, 88.0, 9.0 }, { 17.0, 19.0, 8.0, 89.0, 7.0 },
			{ 11.0, 2.0, 8.0, 99.0, 9.0 }, { 3.0, 11.0, 0.0, 80.0, 4.0 }, { 7.0, 3.0, 11.0, 3.0, 98.0 },
			{ 6.0, 16.0, 1.0, 11.0, 80.0 }, { 10.0, 16.0, 8.0, 2.0, 96.0 }, { 18.0, 5.0, 10.0, 10.0, 95.0 },
			{ 14.0, 19.0, 9.0, 12.0, 93.0 }, { 6.0, 8.0, 9.0, 14.0, 92.0 }, { 2.0, 4.0, 8.0, 10.0, 98.0 },
			{ 0.0, 0.0, 18.0, 19.0, 98.0 }, { 14.0, 19.0, 8.0, 7.0, 85.0 }, { 8.0, 1.0, 5.0, 8.0, 90.0 }, };

	double[][] lowD = new double[][] { { -0.39354151116890057, -0.7952756839724686 },
			{ -0.40400049737573834, -0.8949245360386429 }, { -0.5611889016334022, -0.8128250619708629 },
			{ -0.365074707599201, -0.8800606279683693 }, { -0.4476434682965912, -0.8869304860499643 },
			{ -0.6346420099329199, -0.8999038706487217 }, { -0.2979381359729923, -0.6852850404441032 },
			{ -0.3903207420038042, -0.7768117528608518 }, { -0.43005848692016013, -0.7152641814452001 },
			{ -0.5428864469305704, -0.8383172921132906 }, { -0.9682937981453776, 0.3791483278879353 },
			{ -0.9419344962363572, 0.36629868955942074 }, { -0.9920487692855224, 0.35940232136957934 },
			{ -1.0023528882555355, 0.36470102018691025 }, { -0.8843121521763111, 0.26188604920138125 },
			{ -1.0203647716773898, 0.3424262482072929 }, { -1.2282921350945393, 0.3541928542816095 },
			{ -0.9936235934639299, 0.440109546931751 }, { -1.0453060738063784, 0.35333933375684073 },
			{ -0.9722298654262745, 0.4560639029901129 }, { 1.1172915545637832, 0.4180976395244194 },
			{ 1.00271622690588, 0.3324122425357596 }, { 0.9565504617064304, 0.4048689712109268 },
			{ 0.9324198425899909, 0.30201049166656313 }, { 1.090933738874175, 0.2706324099837015 },
			{ 0.9640774124206212, 0.5005790500824296 }, { 1.0904985455304397, 0.3353812425334171 },
			{ 0.8213449696695067, 0.39740318595067825 }, { 1.1790660763921248, 0.35419285428161096 },
			{ 0.8090775422461767, 0.3523862134491798 }, { -0.3428735032715715, -0.7180511422373163 },
			{ -0.5346409115060673, -0.6385735369547922 }, { -0.30670289794060823, -0.46002531801701424 },
			{ -0.47144149597842105, -0.5546060286546564 }, { -0.500246233288602, -0.7507466706786623 },
			{ -0.35410479510421733, -0.49834775416275995 }, { -0.47288317013924597, -0.8175845982923662 },
			{ -0.5272309110556007, -0.5812226393168729 }, { -0.3930586354957579, -0.7506209212995085 },
			{ -0.607920035373249, -0.6752132037660927 }, { -0.349690504565485, -0.6311324440079344 },
			{ -0.6318667075270546, -0.5963456757590766 }, { -0.50675690057673, -0.5382530564290162 },
			{ -0.38175355644059605, -0.6781843597738286 }, { -0.5126284954873851, -0.5260245667402655 },
			{ -0.42601726206616075, -0.60782171364092 }, { -0.41290400840475183, -0.6432180998277084 },
			{ -0.20297097627281516, -0.5782073377662229 }, { -0.5293157794375508, -0.5208344933879547 },
			{ -0.4404090442947072, -0.7233227216142362 }, };

	double[] weights = new double[] { .2, .2, .2, .2, .2 };

	@Test
	@Ignore
	public void testMds() {
		System.out.println("Running testMds");
		try {
			double[][] newLowD = MDS.mds(highD);
			for (double[] point : newLowD) {
				for (double dim : point)
					System.out.print(dim + " ");
				System.out.println();
			}
		} catch (Exception e) {
			e.printStackTrace();
			fail("Exception occurred");
		}
	}

	@Test
	@Ignore
	public void testInvMds() {
		System.out.println("Running testInvMds");
		try {
			double[] newWeights = MDS.invMds(highD, lowD, weights);
			for (double d : newWeights)
				System.out.print(d + " ");
			System.out.println();

			// double[][] newLowD = MDS.mds(highD, newWeights);
			// for (double[] point : newLowD) {
			// for (double dim : point)
			// System.out.print(dim + " ");
			// System.out.println();
			// }
		} catch (Exception e) {
			e.printStackTrace();
			fail("Exception occurred");
		}
	}

	@Test
	// @Ignore
	public void testVerifyInvMds() {
		System.out.println("Running testVerifyInvMds");

		int numClusters = 5;
		int pointsPerCluster = 10;
		int iterations = 500;
		int[] misses = new int[numClusters];
		Random rand = new Random();

		for (int count = 0; count < iterations; count++) {
			// Generate the high D data, 5 clusters of 5D data
			double[][][] clusters = new double[numClusters][pointsPerCluster][numClusters];
			for (int i = 0; i < numClusters; i++) {
				for (int j = 0; j < pointsPerCluster; j++) {
					for (int k = 0; k < numClusters; k++) {
						if (k == i) {
							// High in this dimension
							clusters[i][j][k] = rand.nextInt(20) + 80;
						} else {
							// Low in this dimension
							clusters[i][j][k] = rand.nextInt(20);
						}
					}
				}
			}

			// Combine into a single set of points
			double[][] combinedHighD = new double[numClusters * pointsPerCluster][numClusters];
			for (int i = 0; i < numClusters; i++) {
				for (int j = 0; j < pointsPerCluster; j++) {
					for (int k = 0; k < numClusters; k++) {
						combinedHighD[i * pointsPerCluster + j][k] = clusters[i][j][k];
					}
				}
			}

			double[] weights = genWeights(numClusters, rand);
			double weightedLowD[][] = MDS.mds(combinedHighD, weights);
//			System.out.println("Weights:" + Arrays.toString(weights));
//			System.out.println("Weight order:" + Arrays.toString(arrayOrder(weights)));


			double[] newWeights = MDS.invMds(combinedHighD, weightedLowD, "euclidean");
//			System.out.println("Calculated weights:" + Arrays.toString(newWeights));
//			System.out.println("Weight order:" + Arrays.toString(arrayOrder(newWeights)));
			
			int[] originalOrder = arrayOrder(weights);
            int[] newOrder = arrayOrder(newWeights);
            for (int i=0; i < numClusters; i++) {
                if (originalOrder[i] != newOrder[i])
                    misses[i]++;
            }
        }
        
        System.out.println("Misses:");
        for (int i=0; i < misses.length; i++) {
            System.out.printf("%.3f " , ((double)misses[i]) / iterations);
        }
	}

	private double[] genWeights(int dimensions) {
		return genWeights(dimensions, new Random());
	}

	private double[] genWeights(int dimensions, Random rand) {
		double[] weights = new double[dimensions];

		// Generate random weights
		for (int i = 0; i < dimensions; i++) {
			weights[i] = rand.nextDouble();
		}

		// Now normalize them so they sum to 1
		return Util.scaleVector(weights);
	}

	private int[] arrayOrder(double[] input) {
		Integer[] indexes = new Integer[input.length];

		final double[] values = input;

		for (int i = 0; i < indexes.length; i++) {
			indexes[i] = i;
		}

		Arrays.sort(indexes, new Comparator<Integer>() {
			public int compare(Integer index1, Integer index2) {
				if (values[index1] > values[index2])
					return 1;
				else
					return -1;
			}
		});

		int[] ret = new int[indexes.length];
		for (int i = 0; i < ret.length; i++) {
			ret[i] = indexes[i];
		}

		return ret;
	}

	@Test
	@Ignore
	public void testUtil() {
		System.out.println("Running testUtil");
		try {
			double dist = Util.dist(highD[0], highD[1], weights, "euclidean");
			// System.out.println(dist);

			dist = Util.dist(highD[0], highD[1], weights, "cosine");
			// System.out.println(dist);

			double[][] pdist = Util.pairwiseDist(new double[][] { { 0, 0 }, { 1, 1 } }, new double[] { 1, 1 },
					"euclidean");
			for (double[] d : pdist)
				System.out.println(Arrays.toString(d));
			System.out.println();

			pdist = Util.pairwiseDist(new double[][] { { 0, 0, 0, 0 }, { 1, 1, 1, 1 } },
					new double[] { .25, .25, .25, .25 }, "euclidean");
			for (double[] d : pdist)
				System.out.println(Arrays.toString(d));
			System.out.println();

			pdist = Util.pairwiseDist(new double[][] { { 0, 0 }, { .5, .5 } }, new double[] { 1, 1 }, "euclidean");
			for (double[] d : pdist)
				System.out.println(Arrays.toString(d));
			System.out.println();

			pdist = Util.pairwiseDist(
					new double[][] { { 0, 0, 0, 0 },
							{ Math.sqrt(.25), Math.sqrt(.25), Math.sqrt(.25), Math.sqrt(.25) } },
					new double[] { 1, 1, 1, 1 }, "euclidean");
			for (double[] d : pdist)
				System.out.println(Arrays.toString(d));
			System.out.println();

			System.out.println("Weighted pdist:");
			pdist = Util.pairwiseDist(lowD, new double[] { .5, .5 });
			for (int i = 0; i < 4; i++)
				System.out.println(Arrays.toString(pdist[i]));
			System.out.println();

			System.out.println("Scaled position pdist:");
			double[][] newLowD = new double[lowD.length][2];
			for (int i = 0; i < newLowD.length; i++) {
				for (int j = 0; j < 2; j++) {
					newLowD[i][j] = lowD[i][j] * Math.sqrt(.5);
				}
			}
			pdist = Util.pairwiseDist(lowD, new double[] { 1, 1 });
			for (int i = 0; i < 4; i++)
				System.out.println(Arrays.toString(pdist[i]));
			System.out.println();

		} catch (Exception e) {
			e.printStackTrace();
			fail("Exception occurred");
		}
	}
}
