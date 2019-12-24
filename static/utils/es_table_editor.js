
function open_es_table_editor(dialog) {

    var contents = [
        "<div class=\"dropdown-container\">",
        "    <div class=\"dropdown-button noselect\">",
        "        <div class=\"dropdown-label\">States</div>",
        "        <div class=\"dropdown-quantity\">(<span class=\"quantity\">Any</span>)</div>",
        "        <i class=\"fa fa-filter\"></i>",
        "    </div>",
        "    <div class=\"dropdown-list\" style=\"display: none;\">",
        "        <input type=\"search\" placeholder=\"Search states\" class=\"dropdown-search\"/>",
        "        <ul id=\"assetlist\"></ul>",
        "    </div>",
        "</div>",
        "<div class=\"dropdown-container\">",
        "    <div class=\"dropdown-button noselect\">",
        "        <div class=\"dropdown-label\">States</div>",
        "        <div class=\"dropdown-quantity\">(<span class=\"quantity\">Any</span>)</div>",
        "        <i class=\"fa fa-filter\"></i>",
        "    </div>",
        "    <div class=\"dropdown-list\" style=\"display: none;\">",
        "        <input type=\"search\" placeholder=\"Search states\" class=\"dropdown-search\"/>",
        "        <ul id=\"columnlist\"></ul>",
        "    </div>",
        "</div>"
    ].join('');

    dialog.setContent(contents);


   // Events
    $('.dropdown-container')
        .on('click', '.dropdown-button', function() {
            $(this).siblings('.dropdown-list').toggle();
        })
        .on('input', '.dropdown-search', function() {
            var target = $(this);
            var dropdownList = target.closest('.dropdown-list');
            var search = target.val().toLowerCase();

            if (!search) {
                dropdownList.find('li').show();
                return false;
            }

            dropdownList.find('li').each(function() {
                var text = $(this).text().toLowerCase();
                var match = text.indexOf(search) > -1;
                $(this).toggle(match);
            });
        })
        .on('change', '[type="checkbox"]', function() {
            var container = $(this).closest('.dropdown-container');
            var numChecked = container. find('[type="checkbox"]:checked').length;
            container.find('.quantity').text(numChecked || 'Any');
        });

    // JSON of States for demo purposes
    var usStates = [
        { name: 'ALABAMA', abbreviation: 'AL'},
        { name: 'ALASKA', abbreviation: 'AK'},
        { name: 'AMERICAN SAMOA', abbreviation: 'AS'},
        { name: 'ARIZONA', abbreviation: 'AZ'},
        { name: 'ARKANSAS', abbreviation: 'AR'},
        { name: 'CALIFORNIA', abbreviation: 'CA'},
        { name: 'COLORADO', abbreviation: 'CO'},
        { name: 'CONNECTICUT', abbreviation: 'CT'},
        { name: 'DELAWARE', abbreviation: 'DE'},
        { name: 'DISTRICT OF COLUMBIA', abbreviation: 'DC'},
        { name: 'FEDERATED STATES OF MICRONESIA', abbreviation: 'FM'},
        { name: 'FLORIDA', abbreviation: 'FL'},
        { name: 'GEORGIA', abbreviation: 'GA'},
        { name: 'GUAM', abbreviation: 'GU'},
        { name: 'HAWAII', abbreviation: 'HI'},
        { name: 'IDAHO', abbreviation: 'ID'},
        { name: 'ILLINOIS', abbreviation: 'IL'},
        { name: 'INDIANA', abbreviation: 'IN'},
        { name: 'IOWA', abbreviation: 'IA'},
        { name: 'KANSAS', abbreviation: 'KS'},
        { name: 'KENTUCKY', abbreviation: 'KY'},
        { name: 'LOUISIANA', abbreviation: 'LA'},
        { name: 'MAINE', abbreviation: 'ME'},
        { name: 'MARSHALL ISLANDS', abbreviation: 'MH'},
        { name: 'MARYLAND', abbreviation: 'MD'},
        { name: 'MASSACHUSETTS', abbreviation: 'MA'},
        { name: 'MICHIGAN', abbreviation: 'MI'},
        { name: 'MINNESOTA', abbreviation: 'MN'},
        { name: 'MISSISSIPPI', abbreviation: 'MS'},
        { name: 'MISSOURI', abbreviation: 'MO'},
        { name: 'MONTANA', abbreviation: 'MT'},
        { name: 'NEBRASKA', abbreviation: 'NE'},
        { name: 'NEVADA', abbreviation: 'NV'},
        { name: 'NEW HAMPSHIRE', abbreviation: 'NH'},
        { name: 'NEW JERSEY', abbreviation: 'NJ'},
        { name: 'NEW MEXICO', abbreviation: 'NM'},
        { name: 'NEW YORK', abbreviation: 'NY'},
        { name: 'NORTH CAROLINA', abbreviation: 'NC'},
        { name: 'NORTH DAKOTA', abbreviation: 'ND'},
        { name: 'NORTHERN MARIANA ISLANDS', abbreviation: 'MP'},
        { name: 'OHIO', abbreviation: 'OH'},
        { name: 'OKLAHOMA', abbreviation: 'OK'},
        { name: 'OREGON', abbreviation: 'OR'},
        { name: 'PALAU', abbreviation: 'PW'},
        { name: 'PENNSYLVANIA', abbreviation: 'PA'},
        { name: 'PUERTO RICO', abbreviation: 'PR'},
        { name: 'RHODE ISLAND', abbreviation: 'RI'},
        { name: 'SOUTH CAROLINA', abbreviation: 'SC'},
        { name: 'SOUTH DAKOTA', abbreviation: 'SD'},
        { name: 'TENNESSEE', abbreviation: 'TN'},
        { name: 'TEXAS', abbreviation: 'TX'},
        { name: 'UTAH', abbreviation: 'UT'},
        { name: 'VERMONT', abbreviation: 'VT'},
        { name: 'VIRGIN ISLANDS', abbreviation: 'VI'},
        { name: 'VIRGINIA', abbreviation: 'VA'},
        { name: 'WASHINGTON', abbreviation: 'WA'},
        { name: 'WEST VIRGINIA', abbreviation: 'WV'},
        { name: 'WISCONSIN', abbreviation: 'WI'},
        { name: 'WYOMING', abbreviation: 'WY' }
    ];

    // <li> template
    var stateTemplate = _.template(
        '<li>' +
            '<input name="<%= abbreviation %>" type="checkbox">' +
            '<label for="<%= abbreviation %>"><%= capName %></label>' +
        '</li>'
    );



    // Populate list with states
    _.each(usStates, function(s) {
        s.capName = _.startCase(s.name.toLowerCase());
        element = document.getElementById('ullist');
        li = stateTemplate(s);
        $('#assetlist').append(stateTemplate(s));
    });





//    dialog.setLocation([ 50, 30 ]);
//    dialog.setSize([ 500, 300 ]);

    dialog.open();
}