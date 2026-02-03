#include <exception>
#include <iostream>
#include <stdexcept>

#include "cxxopts.hpp"
#include "loguru.hpp"
#include "nlohmann/json.hpp"

#include "teds_manager.h"

void set_loglevel(std::string level) {
  if (level == "info") {
    loguru::g_stderr_verbosity = loguru::Verbosity_INFO;
  } else if (level == "warning") {
    loguru::g_stderr_verbosity = loguru::Verbosity_WARNING;
  } else if (level == "error") {
    loguru::g_stderr_verbosity = loguru::Verbosity_ERROR;
  } else if (level == "fatal") {
    loguru::g_stderr_verbosity = loguru::Verbosity_FATAL;
  } else {
    throw std::invalid_argument("Unsupported log level: " + level);
  }
}

int main(int argc, char *argv[]) {
  try {
    // Initialize loguru
    loguru::init(argc, argv);

    // Initialize cxxopts
    cxxopts::Options options("docling-metric-teds", "Compute Tree Edit Distance Score");
    options.add_options()("a,input-a-file", "Input A file in bracket notation",
                          cxxopts::value<std::string>())(
        "b,input-b-file", "Input B file in bracket notation", cxxopts::value<std::string>())(
        "l,loglevel", "loglevel [error;warning;success;info]",
        cxxopts::value<std::string>())("V,version", "Show version")("h,help", "Print usage");
    auto cli = options.parse(argc, argv);

    // Set the log level
    std::string level = "info";
    if (cli.count("loglevel")) {
      level = cli["loglevel"].as<std::string>();

      // Convert the string to lowercase
      std::transform(level.begin(), level.end(), level.begin(),
                     [](unsigned char c) { return std::tolower(c); });
    }
    set_loglevel(level);

    // Help option or no arguments provided
    if (cli.count("help")) {
      LOG_F(INFO, "%s", options.help().c_str());
      return 0;
    }

    // Show version
    if (cli.count("version")) {
      LOG_F(INFO, "Version: %d.%d.%d", PROJECT_VERSION_MAJOR, PROJECT_VERSION_MINOR,
            PROJECT_VERSION_PATCH);
      return 0;
    }

    // Load bracket files and compute TEDS
    if (cli.count("input-a-file") && cli.count("input-b-file")) {
      std::string file_a_fn = cli["input-a-file"].as<std::string>();
      std::string file_b_fn = cli["input-b-file"].as<std::string>();
      LOG_F(INFO, "Input A file: %s", file_a_fn.c_str());
      LOG_F(INFO, "Input B file: %s", file_b_fn.c_str());
      std::string bracket_a, bracket_b;
      std::ifstream file_a(file_a_fn);
      std::getline(file_a, bracket_a);
      file_a.close();
      std::ifstream file_b(file_b_fn);
      std::getline(file_b, bracket_b);
      file_b.close();

      // Compute TEDs
      docling::TEDSManager manager;
      docling::TEDSSampleEvaluation eval_sample =
          manager.evaluate_sample("test", bracket_a, bracket_b);
      LOG_F(INFO, "eval_sample error_id: %d", eval_sample.error_id);
      LOG_F(INFO, "eval_sample error_msg: %s", eval_sample.error_msg.c_str());
      LOG_F(INFO, "eval_sample tree A size: %d", eval_sample.tree_a_size);
      LOG_F(INFO, "eval_sample tree B size: %d", eval_sample.tree_b_size);
      LOG_F(INFO, "eval_sample TEDS: %f", eval_sample.teds);

      return 0;
    }

    LOG_F(ERROR, "Missing CLI input");
    LOG_F(INFO, "%s", options.help().c_str());
    return 1;
  } catch (const cxxopts::exceptions::exception &e) {
    LOG_F(ERROR, "Error parsing options: %s", e.what());
    return 2;
  }
}
