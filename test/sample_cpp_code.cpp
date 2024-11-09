#include <random>

std::vector<std::string> Split(std::string str, char delimiter) {
  std::vector<std::string> result;
  std::string current;

  for (char chr : str) {
    if (chr == delimiter) {
      // When delimiter is encountered, push the current substring to the result
      if (!current.empty()) {
        result.push_back(current);
        current.clear(); // Reset the current substring
      }
    } else {
      // If the character is not a delimiter, append it to the current substring
      current += chr;
    }
  }

  // Add the last part of the string
  if (!current.empty()) {
    result.push_back(current);
  }

  return result;
}

int GetPlayerIdFromName(std::string player_name) {
  std::vector<std::string> player = Split(player_name, '_');

  if (player.size() == 2) {
    return std::stoi(player[1]);
  }

  return -1;
}

// Returns an integer between and including 0 and n
int GetRandomInt(int n) {
  std::random_device rand_dev;
  std::mt19937 gen(rand_dev());
  std::uniform_int_distribution<> distr(0, n);

  return distr(gen);
}
