(function () {
  function initScript() {
    if (typeof django.jQuery === "undefined") {
      setTimeout(initScript, 100);
      return;
    }

    var $ = django.jQuery;

    $(document).ready(function () {
      const rarityChances = {
        pity: 0.0,
        earlydays: 0.0,
        developer: 0.0,
        artist: 0.0,
        founder: 0.0,
        common: 70.0,
        uncommon: 25.0,
        rare: 5.0,
        epic: 1.0,
        legendary: 0.01,
        exotic: 0.001,
        mythic: 0.0001,
        novelty: 0.00001,
      };

      const rarityMaxInstances = {
        pity: 0,
        earlydays: 0,
        developer: 0,
        artist: 0,
        founder: 0,
        common: 1000000000,
        uncommon: 500000000,
        rare: 100000000,
        epic: 10000000,
        legendary: 1000000,
        exotic: 100000,
        mythic: 10000,
        novelty: 1,
      };

      function formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
      }

      function getLikelihoodText(chance) {
        if (chance === 0) return "0% (Not rollable)";
        const fraction = chance / 100;
        const likelihood = 1 / fraction;
        let likelihoodText;
        if (Number.isInteger(likelihood)) {
          likelihoodText = `1 in ${formatNumber(Math.round(likelihood))}`;
        } else if (likelihood < 100) {
          likelihoodText = `1 in ${likelihood.toFixed(1)}`;
        } else {
          likelihoodText = `1 in ${formatNumber(Math.round(likelihood))}`;
        }
        return Number.isInteger(chance) ? `${chance}%` : `${chance}% (about ${likelihoodText})`;
      }

      function updateFields() {
        const rarity = $("#id_rarity").val();
        const rollChance = rarityChances[rarity] || 0.0;
        const maxInstances = rarityMaxInstances[rarity] || 0;

        const rollChanceText = getLikelihoodText(rollChance);
        const maxInstancesText = maxInstances > 0 ? formatNumber(maxInstances) : "Unlimited";

        $(".field-formatted_roll_chance .readonly").text(rollChanceText);
        $(".field-formatted_max_instances .readonly").text(maxInstancesText);
      }

      updateFields();
      $("#id_rarity").change(updateFields);
    });
  }

  initScript();
})();
