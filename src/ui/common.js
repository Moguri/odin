Chart.defaults.global.scaleOverride = true;
Chart.defaults.global.scaleSteps = 5;
Chart.defaults.global.scaleStepWidth = 0.2;
Chart.defaults.global.scaleStartValue = 0;

var stance_template =
'<li>' +
'   <div id="%DIVID%"class="panel panel-default">' +
'       <div class="panel-heading">%NAME%</div>' +
'       <div class="panel-body">' +
'          <canvas id="%CANVASID%"></canvas>' +
'       </div>' +
'   </div>' +
'</li>';

function setupSpells(list_id, spell_list) {
    $('#' + list_id).empty();

    $.each(spell_list, function(i, v) {
        canvas_id = "c" + list_id + i;
        div_id = "d" + list_id + i;
        html = stance_template.replace(/%NAME%/, v.name)
                              .replace(/%DIVID%/, div_id)
                              .replace(/%CANVASID%/, canvas_id);
        $('#' + list_id).append(html);

        canvas = $('#' + canvas_id).get(0);

        chart_data = {
            labels: ["Movement", "Range", "Damage", "Defense", "Regen", "Speed"],
            datasets: [
                {
                    fillColor: "rgba(0, 256, 0, 0.5)",
                    strokeColor: "rgba(0, 256, 0, 0.8)",
                    data: v.benefit_vector
                },
                {
                    fillColor: "rgba(256, 0, 0, 0.5)",
                    strokeColor: "rgba(256, 0, 0, 0.8)",
                    data: v.cost_vector
                }
            ]
        };
        radar = new Chart(canvas.getContext("2d")).Radar(chart_data, {pointDot: false});
    });
}