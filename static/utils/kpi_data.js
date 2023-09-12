function get_bg_color(idx) {
    let colors = [
        'rgba(255, 99, 132, 0.2)',
        'rgba(54, 162, 235, 0.2)',
        'rgba(255, 206, 86, 0.2)',
        'rgba(75, 192, 192, 0.2)',
        'rgba(153, 102, 255, 0.2)',
        'rgba(255, 159, 64, 0.2)'
    ];
    return colors[idx % colors.length];
}

function createChartOptions(kpi_info) {
    // This function is being called with a parameter kpi_info that is an array with objects for each loaded
    // energy system. It allows side-by-side comparison of different energy system scenarios. The format of the
    // data is shown below

    // console.log(kpi_info);
    // Example KPI object (with just one energy system)
    //    0:
    //        distribution: Array(3)
    //            0: {label: "Warmte", value: 3.3085894444545933e-13}
    //            1: {label: "Electricity", value: 5.774796217681515e-11}
    //            2: {label: "Aardgas", value: 1.3353686339893772e-10}
    //        es_id: "2d8533b2-6b7e-4a70-a6e2-a9720e587d7b"
    //        name: "Total excess production [Percentages]"
    //        scope: "essim kpis"
    //        type: "Distribution"
    //        unit: "Percentages"

    // Other example
    //  0:
    //      es_id: "926fa9a2-9f04-45a8-adfd-813d29acd6c0"
    //      name: "Energy neutrality"
    //      scope: "Untitled Area"
    //      targets: Array(1)
    //          0: {year: 2050, value: 100}
    //      type: "Int"
    //      unit: "N/A"
    //      value: 23

    let type = null;
    let labels = [];
    let datasets = [];
    let options = {};

    // TODO: we now assume that the same KPI in different energy systems has the same type
    let distr_or_value = kpi_info[0].type;

    if (distr_or_value === 'Distribution') {
        let kpi_item = null;
        let dataset_dict = {};
// This works for bar charts, but not for doughnuts
// For barcharts, energysystems are shown side by side
// ---------------------------------------------------
//            for (let i=0; i<kpi_info.length; i++) {
//                kpi_item = kpi_info[i];
//                labels.push(i.toString());      // must be es name (or something like that)
//
//                for (let i=0; i<kpi_item.distribution.length; i++) {
//                    let distr_part = kpi_item.distribution[i]
//
//                    if (distr_part.label in dataset_dict)
//                        dataset_dict[distr_part.label].data.push(distr_part.value)
//                    else {
//                        dataset_dict[distr_part.label] = {
//                            label: distr_part.label,
//                            backgroundColor: this.get_bg_color(i),
//                            data: [distr_part.value]
//                        };
//                    }
//                }
//            }
//
//            for (let lbl in dataset_dict) {
//                datasets.push(dataset_dict[lbl]);
//            }

// This works both for bar charts and doughnuts
// For barcharts, energysystems are mixed per distribution label
// ---------------------------------------------------
        // Create a dict with keys of all distribution labels for the kpi for all energy systems
        let distr_labels_dict = {}
        let num_distr_labels = 0
        for (let i=0; i<kpi_info.length; i++) {
            kpi_item = kpi_info[i];

            for (let j=0; j<kpi_item.distribution.length; j++) {
                if (!(kpi_item.distribution[j].label in distr_labels_dict)) {
                    distr_labels_dict[kpi_item.distribution[j].label] = {
                        backgroundColor: get_bg_color(num_distr_labels),
                        data: {}        // key=es, data=value for that kpi for that es
                    }
                    num_distr_labels = num_distr_labels + 1;
                }
            }
        }
        // console.log(distr_labels_dict);

        // Fill in energy system data
        for (let i=0; i<kpi_info.length; i++) {
            kpi_item = kpi_info[i];

            for (let j=0; j<kpi_item.distribution.length; j++) {
                let distr_part = kpi_item.distribution[j]
                distr_labels_dict[distr_part.label]['data'][kpi_item['es_id']] = distr_part.value;
            }
        }

        // Convert to list to preserve order (Is this required?)
        let label_info_array = [];
        let bgColor_array = [];
        for (let lbl in distr_labels_dict) {
            labels.push(lbl);
            label_info_array.push(distr_labels_dict[lbl]);
            bgColor_array.push(distr_labels_dict[lbl]['backgroundColor'])
        }

        // Now transpose the data structure to a format that chartjs accepts
        // Iterate over all EnergySystems
        for (let i=0; i<kpi_info.length; i++) {
            kpi_item = kpi_info[i];

            let dataset = {}
            // dataset['label'] = i.toString();  // kpi_item['es_id'];
            let label = kpi_item['kpis_description'];
            if (!label) {
                label = i.toString();   // if no kpis_description was given, use an index
            } else {
                // make sure labels are not longer than 10 characters
                if (label.length > 10) {
                    label = label.substring(0, 7) + '...';
                }
            }
            dataset['label'] = label;

            let data = new Array(labels.length);
            data = data.fill(0);
            for (let lbl_info in label_info_array) {
                for (let es_id in label_info_array[lbl_info]['data']) {
                    if (es_id == kpi_item['es_id']) {
                        data[lbl_info] = label_info_array[lbl_info]['data'][es_id];
                    }
                }
            }
            dataset['data'] = data;
            dataset['backgroundColor'] = bgColor_array;
            datasets.push(dataset)
        }

        type = 'bar'
        options = {
            legend: {
                display: true,
                position: 'right',
                labels: {
                    boxWidth: 10,
                    fontSize: 9
                }
            },
            scales: {
//                   xAxes: [{
//                       stacked: false,
//                   }],
                yAxes: [{
//                       stacked: true,
                    ticks: {
                        beginAtZero: true,
//                            maxTicksLimit: 6,
                        callback: function(value) {
                            return formatN(value).toString();
                        }
                    }
                }]
            },
            title: {
                display: true,
                text: kpi_item.name
            }
        }
    } else {
        labels = ['Current value'];

        for (let i=0; i<kpi_info.length; i++) {
            kpi_item = kpi_info[i];
            let target = null;
            if ('targets' in kpi_item) {
                if (kpi_item.targets.length > 0) {
                    target = kpi_item.targets[0].value;
                    type = 'doughnut';
                } else {
                    type = 'bar';
                }
            } else {
                type = 'bar';
            }

            if (type === 'bar') {
                data = [kpi_item.value];
            } else {
                data = [kpi_item.value, target-kpi_item.value];
                if (labels.length < 2) { labels.push('Still to go...'); }
            }

            datasets.push({
                label: labels,
                data: data,
                backgroundColor: [this.get_bg_color(0), this.get_bg_color(1)]
            });
        }

        options = {
            legend: {
                display: false,
            },
            title: {
                display: true,
                text: kpi_item.name
            },
            scales: {
                yAxes: [{
                    ticks: {
                        beginAtZero: true,
//                            maxTicksLimit: 6,
                        callback: function(value) {
                            return formatN(value).toString();
                        }
                    }
                }]
            }
        }
    }

    return {
        type: type,
        data: {
            labels: labels,
            datasets: datasets
        },
        options: options
    };
}