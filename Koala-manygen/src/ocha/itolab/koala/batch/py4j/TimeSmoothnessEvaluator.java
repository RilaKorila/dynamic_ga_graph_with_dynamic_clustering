package ocha.itolab.koala.batch.py4j;

import ocha.itolab.koala.core.mesh.Vertex;
import ocha.itolab.koala.core.data.Node;
import ocha.itolab.koala.core.data.Graph;

import java.util.HashMap;
import java.util.List;
import java.util.stream.Collectors;

public class TimeSmoothnessEvaluator {
    public TimeSmoothnessEvaluator() {
    }

    public static double execute(final double previousInit[], final double init[], final int timestamp,
            final List<List<Integer>> previousDynamicCommunities, final List<List<Integer>> dynamicCommunities) {
        if (previousDynamicCommunities == null) {
            return 0.0;
        }

        // ノードIDのリストをキー、動的コミュニティIDを値とするマッピングを作成
        final HashMap<List<Integer>, Integer> dynamicCommunityIdMap = getDynamicCommunityIdMap(dynamicCommunities);
        final Graph currentGraph = KoalaToSprawlter.getGraph(init, timestamp);
        // GraphのVertex(メタノード)に動的コミュニティIDを割り当てる
        assignDynamicCommunityId(currentGraph, dynamicCommunityIdMap);

        // 1つ前のタイムスタンプでも同様の処理を行う
        final HashMap<List<Integer>, Integer> previousDynamicCommunityIdMap = getDynamicCommunityIdMap(
                previousDynamicCommunities);
        final Graph previousGraph = KoalaToSprawlter.getGraph(previousInit, timestamp - 1);
        assignDynamicCommunityId(previousGraph, previousDynamicCommunityIdMap);

        // 時間平滑性を計算する
        // return calculateTimeSmoothness(previousGraph, currentGraph);
        return calculateTimeSmoothnessWithMultipleMatches(previousGraph, currentGraph);
    }

    /**
     * Vertex(つまりメタノード)に動的コミュニティIDを割り当てる
     * 
     * @param graph                 グラフ
     * @param dynamicCommunityIdMap ノードリストと動的コミュニティIDのマッピング
     */
    private static void assignDynamicCommunityId(final Graph graph,
            final HashMap<List<Integer>, Integer> dynamicCommunityIdMap) {
        for (Vertex vertex : graph.mesh.getVertices()) {
            // Nodeのリストを文字列のリストに変換
            final List<Integer> nodeIds = vertex.getNodes().stream()
                    .map(Node::getId)
                    .sorted()
                    .collect(Collectors.toList());
            Integer dynamicCommunityId = dynamicCommunityIdMap.get(nodeIds);

            if (dynamicCommunityId == null) {
                System.out.println("Warning: No community found for nodes: " + nodeIds);
                continue;
            }
            vertex.setDynamicCommunityId(dynamicCommunityId);
        }
    }

    /**
     * ノードリストと動的コミュニティIDのマッピングを作成する
     * 
     * @param nodes
     * @param dynamicCommunities
     * @return ノードリストがキー、動的コミュニティIDが値のマッピング
     */
    private static HashMap<List<Integer>, Integer> getDynamicCommunityIdMap(
            final List<List<Integer>> dynamicCommunities) {
        final HashMap<List<Integer>, Integer> dynamicCommunityIdMap = new HashMap<>(dynamicCommunities.size());

        for (int i = 0; i < dynamicCommunities.size(); i++) {
            final List<Integer> nodeIds = dynamicCommunities.get(i).stream()
                    .sorted().toList();
            dynamicCommunityIdMap.put(nodeIds, i);
        }

        return dynamicCommunityIdMap;
    }

    /**
     * 時間平滑性を計算する
     * 
     * @param previousGraph 1つ前のタイムスタンプのグラフ
     * @param currentGraph  現在のタイムスタンプのグラフ
     * @return 時間平滑性
     */
    private static double calculateTimeSmoothness(final Graph previousGraph, final Graph currentGraph) {
        double totalDistance = 0.0;

        for (Vertex currentVertex : currentGraph.mesh.getVertices()) {
            for (Vertex previousVertex : previousGraph.mesh.getVertices()) {

                // 同じDynamicCommunityに属しているかどうかを判断
                if (currentVertex.getDynamicCommunityId() == previousVertex.getDynamicCommunityId()) {
                    // 大きいmetanodeほどインパクトが大きいので、metanodeに属するnode数を移動距離に乗算する
                    final double penalty = calculateDistance(currentVertex.getPosition(), previousVertex.getPosition(),
                            10.0) * currentVertex.getNodeNum();
                    totalDistance += penalty;
                }
            }
        }

        // TODO
        // Cursorは1つ前のタイムスタンプのグラフのノード数と現在のタイムスタンプのグラフのノード数の比率を用いて、計算しようとしていたので必要かどうかを確認する。
        return totalDistance;
    }

    /**
     * 時間平滑性を計算する。ただし、同じdynamic_community_idを持つメタノード同士だけでなく、Jaccard係数が閾値以上のメタノード同士も考慮する。
     * ("類似のmetanode"が 1:1 ではなく、1:n の関係になる)
     * 
     * @param previousGraph 1つ前のタイムスタンプのグラフ
     * @param currentGraph  現在のタイムスタンプのグラフ
     * @return 時間平滑性
     */

     private static double calculateTimeSmoothnessWithMultipleMatches(final Graph previousGraph, final Graph currentGraph) {
        double totalDistance = 0.0;
        double similarityThreshold = 0.25; // Jaccard係数の閾値

        for (Vertex currentVertex : currentGraph.mesh.getVertices()) {
            for (Vertex previousVertex : previousGraph.mesh.getVertices()) {

                // metanodeに属するnodeの集合同士でJaccard係数を計算し、閾値以上であれば距離を計算する
                List<Integer> currentNodeIds = currentVertex.getNodes().stream()
                        .map(Node::getId).sorted().collect(Collectors.toList());
                List<Integer> previousNodeIds = previousVertex.getNodes().stream()
                        .map(Node::getId).sorted().collect(Collectors.toList());

                if (calculateJaccardCoefficient(currentNodeIds, previousNodeIds) > similarityThreshold) {
                    // 大きいmetanodeほどインパクトが大きいので、metanodeに属するnode数を移動距離に乗算する
                    final double penalty = calculateDistance(currentVertex.getPosition(), previousVertex.getPosition(),
                            10.0) * currentVertex.getNodeNum();
                    totalDistance += penalty;
                }
            }
        }

        return totalDistance;
    }

    /**
     * 与えられた2つのノードリストのJaccard係数を計算する
     * @param nodes1
     * @param nodes2
     * @return Jaccard係数
     */
    private static double calculateJaccardCoefficient(final List<Integer> nodes1, final List<Integer> nodes2) {
        if (nodes1.isEmpty() || nodes2.isEmpty()) {
            return 0.0;
        }

        // 共通の要素数を計算
        long intersectionSize = nodes1.stream().filter(nodes2::contains).count();
        // 和集合のサイズを計算
        long unionSize = nodes1.size() + nodes2.size() - intersectionSize;

        return (double) intersectionSize / unionSize;
    }   


    /**
     * 2点間のユークリッド距離を計算する
     * 
     * @param p1    点1の座標
     * @param p2    点2の座標
     * @param scale 座標が1以下の場合、ユークリッド距離を取ると小さくなり過ぎてしまうのでscaleで等倍処理する
     * @return 2点間のユークリッド距離
     */
    private static double calculateDistance(final double[] p1, final double[] p2, final double scale) {
        double dx = Math.abs(p1[0] - p2[0]) * scale;
        double dy = Math.abs(p1[1] - p2[1]) * scale;

        return Math.sqrt(dx * dx + dy * dy);
    }

}
