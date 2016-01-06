class Bot
  # Public: creates an instance of the bot.
  #
  # client - the GitHub client. Needs to have the same API as octokit.
  def initialize(client)
    @client = client
  end

  # Public: handles a pull request.
  #
  # payload - the Hash containing the payload of the request.
  def handle_pull_request!(payload)
    repository = payload['repository']['full_name']
    number = payload['number']
    body = payload['pull_request']['body']

    assignee = /\b[rR]\?[:\- ]*@(?<name>[a-zA-Z0-9\-_]+)/.match(body)

    if assignee
      @client.update_issue(repository, number, assignee: assignee[:name])
    end

    author = payload['pull_request']['user']['login']

    if new_contributor?(repository, author)
      @client.add_comment(repository, number, welcome_message(assignee[:name]))
    end
  end

  private

  # Internal: checks if the author is a new contributor.
  def new_contributor?(repository, author)
    contributors = @client.contributors(repository)

    contributors.none? { |contributor| contributor['login'] == author }
  end

  # Internal: builds the welcome message.
  def welcome_message(assignee)
    <<~MSG % assignee
    Thanks for the pull request, and welcome! The Rails team is excited to review your changes, and you should hear from @%s (or someone else) soon.

    If any changes to this PR are deemed necessary, please add them as extra commits. This ensures that the reviewer can see what has changed since they last reviewed the code. Due to the way GitHub handles out-of-date commits, this should also make it reasonably obvious what issues have or haven't been addressed. Large or tricky changes may require several passes of review and changes.

    Please see [the contribution instructions](http://edgeguides.rubyonrails.org/contributing_to_ruby_on_rails.html) for more information.
    MSG
  end
end
