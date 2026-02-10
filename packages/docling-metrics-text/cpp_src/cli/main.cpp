#include <exception>
#include <iostream>
#include <stdexcept>

#include "cxxopts.hpp"
#include "loguru.hpp"

#include "re2/re2.h"

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

void demo_regex() {
  int i;
  std::string s;
  RE2 re("(\\w+):(\\d+)");
  assert(re.ok()); // compiled; if not, see re.error();

  assert(RE2::FullMatch("ruby:1234", re, &s, &i));
  assert(RE2::FullMatch("ruby:1234", re, &s));
  assert(RE2::FullMatch("ruby:1234", re, (void *)NULL, &i));
  assert(!RE2::FullMatch("ruby:123456789123", re, &s, &i));
}

int main(int argc, char *argv[]) {
  try {
    // Initialize loguru
    loguru::init(argc, argv);

    // TODO: Initialize cxxopts
    cxxopts::Options options("docling-metrics-teds", "Compute Tree Edit Distance Score");
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
    // if (cli.count("input-a-file") && cli.count("input-b-file")) {
    //   std::string file_a_fn = cli["input-a-file"].as<std::string>();
    //   std::string file_b_fn = cli["input-b-file"].as<std::string>();
    //   LOG_F(INFO, "Input A file: %s", file_a_fn.c_str());
    //   LOG_F(INFO, "Input B file: %s", file_b_fn.c_str());
    // }
    // LOG_F(ERROR, "Missing CLI input");
    // LOG_F(INFO, "%s", options.help().c_str());

    demo_regex();

    return 1;
  } catch (const cxxopts::exceptions::exception &e) {
    LOG_F(ERROR, "Error parsing options: %s", e.what());
    return 2;
  }
}
