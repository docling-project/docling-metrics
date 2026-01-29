#include <iostream>

#include "nlohmann/json.hpp"
#include "loguru.hpp"
#include "cxxopts.hpp"

#include "teds_manager.h"


int main(int argc, char* argv[]) {
  int orig_argc = argc;

  // Initialize loguru
  loguru::init(argc, argv);

  try {
      cxxopts::Options options("docling-metric-teds", "Compute Tree Edit Distance Score");

      // Define the options
      options.add_options()
        ("g,gt-file", "Input ground truth file in bracket notation", cxxopts::value<std::string>())
        ("p,pred-file", "Input predictions file in bracket notation", cxxopts::value<std::string>())
        ("l,loglevel", "loglevel [error;warning;success;info]", cxxopts::value<std::string>())
        ("v,version", "Show version")
        ("h,help", "Print usage");

      // Parse command line arguments
      auto result = options.parse(argc, argv);

      // TODO: Check if orig_argc is needed
      if (orig_argc == 1) {
          LOG_S(INFO) << argc;
          LOG_F(ERROR, "Either input (-i) or config (-c) must be specified.");
          LOG_F(INFO, "%s", options.help().c_str());
          return 1;
      }

      // Help option or no arguments provided
      if (result.count("help")) {
        LOG_F(INFO, "%s", options.help().c_str());
        return 0;
      }
      
      // Show version
      if (result.count("version")) {
        LOG_F(INFO, "Version: %d.%d.%d", PROJECT_VERSION_MAJOR, PROJECT_VERSION_MINOR, PROJECT_VERSION_PATCH);
        return 0;
      }
      
      // Load bracket files and compute TEDS
      std::string gt_file_fn = result["gt-file"].as<std::string>();
      std::string pred_file_fn = result["pred-file"].as<std::string>();
      LOG_F(INFO, "GT file: %s", gt_file_fn.c_str());
      LOG_F(INFO, "Pred file: %s", pred_file_fn.c_str());
      std::string gt_bracket, pred_bracket;
      std::ifstream gt_file(gt_file_fn);
      std::getline(gt_file, gt_bracket);
      gt_file.close();
      std::ifstream pred_file(pred_file_fn);
      std::getline(pred_file, pred_bracket);
      pred_file.close();

      // Compute TEDs
      docling::TEDSManager manager;
      docling::TEDSSampleEvaluation eval_sample = manager.eval_sample("test", gt_bracket, pred_bracket);
      LOG_F(INFO, "eval_sample error_id: %d", eval_sample.error_id);
      LOG_F(INFO, "eval_sample error_msg: %s", eval_sample.error_msg.c_str());
      LOG_F(INFO, "eval_sample gt_tree_size: %d", eval_sample.gt_tree_size);
      LOG_F(INFO, "eval_sample pred_tree_size: %d", eval_sample.pred_tree_size);
      LOG_F(INFO, "eval_sample TEDS: %f", eval_sample.teds);

  } catch (const cxxopts::exceptions::exception& e) {
    LOG_F(ERROR, "Error parsing options: %s", e.what());
    return 1;
  }

  return 0;
}

