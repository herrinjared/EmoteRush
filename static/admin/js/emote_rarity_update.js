(function ($) {
  // Wait for django.jQuery to be available
  function initScript() {
    if (typeof django.jQuery === "undefined") {
      setTimeout(initScript, 100);
      return;
    }

    var $ = django.jQuery;

    $(document).ready(function () {
      // Rarity mapping from model
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

      // Function to format numbers with commas
      function formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
      }

      // Update display function
      function updateFields() {
        const rarity = $("#id_rarity").val();
        const rollChance = rarityChances[rarity] || 0.0;
        const maxInstances = rarityMaxInstances[rarity] || 0;

        const rollChanceText = Number.isInteger(rollChance) ? `${rollChance}%` : `${rollChance}%`;
        const maxInstancesText = maxInstances > 0 ? formatNumber(maxInstances) : "Unlimited";

        $(".field-formatted_roll_chance .readonly").text(rollChanceText);
        $(".field-formatted_max_instances .readonly").text(maxInstancesText);
      }

      // Initial update
      updateFields();

      // Update on rarity change
      $("#id_rarity").change(updateFields);
    });
  }

  initScript();
})();
