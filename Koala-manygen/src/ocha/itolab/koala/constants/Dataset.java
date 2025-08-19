package ocha.itolab.koala.constants;

public enum Dataset {
    FACEBOOK(
            "/Users/ayana/vis/dynamic_ga_graph_with_dynamic_clustering/data/facebook/",
            "/Users/ayana/vis/dynamic_ga_graph_with_dynamic_clustering/data/facebook/filtered_coms/",
            "facebook"),
    CIT_HEP_PH(
            "/Users/ayana/vis/dynamic_ga_graph_with_dynamic_clustering/data/Cit-HepPh/",
            "/Users/ayana/vis/dynamic_ga_graph_with_dynamic_clustering/data/Cit-HepPh/filtered_coms/",
            "Cit-HepPh"),
    TIMESMOOTHNESS_SAMPLE(
            "/Users/ayana/vis/dynamic_ga_graph_with_dynamic_clustering/data/timesmoothnessSample/",
            "/Users/ayana/vis/dynamic_ga_graph_with_dynamic_clustering/data/timesmoothnessSample/filtered_coms/",
            "timesmoothnessSample");

    private String dataDirPath;
    private String comsPath;
    private String name;

    Dataset(final String dataDirPath, final String comsPath, final String name) {
        this.dataDirPath = dataDirPath;
        this.comsPath = comsPath;
        this.name = name;
    }

    public String getDataDirPath() {
        return this.dataDirPath;
    }

    public String getComsPath() {
        return this.comsPath;
    }

    public String getName() {
        return this.name;
    }
}
