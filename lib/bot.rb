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

    assignee = /\b[rR]\?[:\- ]*@([a-zA-Z0-9\-_]+)/.match(body)[1]

    @client.update_issue(repository, number, assignee: assignee)
  end
end
